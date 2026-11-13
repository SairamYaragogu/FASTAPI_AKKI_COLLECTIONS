from typing import List, Optional
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    sno: Optional[int] = None
    category: str
    subcategory: str
    title: str
    description: Optional[str] = None
    price: float
    mrp: Optional[float] = None
    discount_pct: Optional[int] = None
    rating: Optional[float] = 4.3
    reviews_count: Optional[int] = 120
    image_urls: List[str] = Field(default_factory=list)
    primary_image: Optional[str] = None
    stock_status: Optional[str] = "In Stock"

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sno: Optional[int] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    discount_pct: Optional[int] = None
    image_urls: Optional[List[str]] = None
    primary_image: Optional[str] = None
    stock_status: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CategorySummary(BaseModel):
    category: str
    count: int
    subcategories: List[str]

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    authenticated: bool
    message: str
    token: Optional[str] = None

class ExcelUploadResponse(BaseModel):
    success: bool
    message: str
    inserted_count: int
    updated_count: int
    total_records: int
