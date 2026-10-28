import io
import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import FASTAPI_HOST, FASTAPI_PORT, ADMIN_USERNAME, ADMIN_PASSWORD
from database import init_db
from models import (
    ProductResponse, ProductCreate, CategorySummary,
    AdminLoginRequest, AdminLoginResponse, ExcelUploadResponse
)
from excel_service import parse_stock_excel
import repository as repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("akki_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    logger.info("Initializing database schema...")
    try:
        init_db()
        logger.info("Database schema verified.")
        
        # Check if products already exist, if not, auto-seed from data/stock_entry.xlsx
        stats = repo.get_stats()
        if stats["total_products"] == 0:
            stock_path = os.path.join(os.path.dirname(__file__), "data", "stock_entry.xlsx")
            if os.path.exists(stock_path):
                logger.info(f"Auto-seeding initial inventory from {stock_path}...")
                products = parse_stock_excel(stock_path)
                ins, upd = repo.bulk_upsert_products(products)
                logger.info(f"Auto-seed completed: {ins} inserted, {upd} updated.")
    except Exception as e:
        logger.error(f"Error during startup initialization: {e}")
    yield
    logger.info("Shutting down backend...")

app = FastAPI(
    title="AKKI LATEST COLLECTIONS - Backend API",
    description="FastAPI Backend for Akki Latest Collections E-Commerce Application",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Streamlit and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["General"])
def root():
    return {
        "app": "AKKI LATEST COLLECTIONS API",
        "status": "Online",
        "documentation": "/docs",
        "endpoints": {
            "products": "/api/products",
            "categories": "/api/categories",
            "subcategories": "/api/subcategories",
            "stats": "/api/stats",
            "upload_excel": "/api/admin/upload-excel"
        }
    }

@app.get("/api/health", tags=["General"])
def health_check():
    stats = repo.get_stats()
    return {"status": "ok", "stats": stats}

@app.get("/api/stats", tags=["Products"])
def get_dashboard_stats():
    return repo.get_stats()

@app.get("/api/categories", response_model=List[CategorySummary], tags=["Categories"])
def get_categories():
    """Retrieve all categories, product counts, and subcategories."""
    return repo.get_categories_summary()

@app.get("/api/subcategories", response_model=List[str], tags=["Categories"])
def get_subcategories(category: Optional[str] = Query(None, description="Category name to filter subcategories")):
    """Retrieve subcategories for a given category (or all if category is omitted)."""
    return repo.get_subcategories(category=category)

@app.get("/api/products", response_model=List[ProductResponse], tags=["Products"])
def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    search: Optional[str] = Query(None, description="Search keyword in title, category or description"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    sort_by: Optional[str] = Query(None, description="Sort order: price_asc, price_desc, rating_desc, discount_desc, newest"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Retrieve product listings with filters and sorting."""
    return repo.get_products(
        category=category,
        subcategory=subcategory,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )

@app.get("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product_detail(product_id: int):
    """Retrieve full details of a specific product by ID."""
    product = repo.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found.")
    return product

@app.delete("/api/products/{product_id}", tags=["Products"])
def delete_product(product_id: int):
    """Delete a specific product by ID."""
    success = repo.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found.")
    return {"message": "Product successfully deleted.", "id": product_id}

@app.post("/api/admin/login", response_model=AdminLoginResponse, tags=["Admin"])
def admin_login(creds: AdminLoginRequest):
    """Authenticate administrator to access the admin dashboard."""
    if creds.username == ADMIN_USERNAME and creds.password == ADMIN_PASSWORD:
        return AdminLoginResponse(
            authenticated=True,
            message="Admin authentication successful.",
            token="akki-admin-secure-session-token"
        )
    return AdminLoginResponse(
        authenticated=False,
        message="Invalid admin username or password.",
        token=None
    )

@app.post("/api/admin/upload-excel", response_model=ExcelUploadResponse, tags=["Admin"])
async def upload_stock_excel(file: UploadFile = File(...)):
    """
    Upload and parse stock_entry.xlsx to automatically update the MySQL database inventory.
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload an Excel (.xlsx or .xls) file."
        )

    try:
        contents = await file.read()
        file_buffer = io.BytesIO(contents)
        products = parse_stock_excel(file_buffer)
        
        if not products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid product rows could be extracted from the file."
            )

        inserted, updated = repo.bulk_upsert_products(products)

        # Also backup/save uploaded file to data/stock_entry.xlsx
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        backup_path = os.path.join(data_dir, "stock_entry.xlsx")
        with open(backup_path, "wb") as f:
            f.write(contents)

        return ExcelUploadResponse(
            success=True,
            message=f"Stock data updated successfully: {inserted} new items added, {updated} existing items refreshed.",
            inserted_count=inserted,
            updated_count=updated,
            total_records=len(products)
        )
    except Exception as e:
        logger.error(f"Error processing Excel upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Excel file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=True)
