# AKKI LATEST COLLECTIONS 🛍️

Full-stack E-Commerce Application inspired by **Flipkart** UI aesthetics, built with **Python**, **FastAPI**, **MySQL**, and **Streamlit**.

---

## 🌟 Features

- **Flipkart Design Aesthetics**:
  - Flipkart Blue (`#2874f0`), Yellow (`#ff9f00`), Orange (`#fb641b`), Green (`#388e3c`), and clean card elevation shadows.
  - Explore Plus brand logo badge (`Explore Plus ✦`).
  - Search bar with instant keyword matching across title, category, and fabric.
- **Dynamic Category & Subcategory Filtering**:
  - Top category pills: `All`, `Saree 🥻`, `Dress Material 👗`, `Dress ✨`, `Cotton Dress 🌸`.
  - Subcategories dynamically adapt based on selected category (e.g., *Net Saree, Chanderi Saree, Soft Silk Saree, Banarasi Saree, etc.*).
- **Flipkart Product Cards**:
  - Cloudinary product images with smooth hover zoom.
  - Green star rating badge (e.g. `4.4 ★`) with review counts.
  - Selling Price (`₹`), Strikethrough MRP, and green Discount Percentage tag (`36% off`).
  - Free Delivery and Special Price badges.
- **Flipkart-Style Product Details Page**:
  - Image gallery with clickable multi-angle thumbnail preview.
  - Available Offers section (Bank discounts, special pricing, partner offers, No Cost EMI).
  - Delivery estimations and 7-day replacement assurance.
  - Detailed product specifications table (Catalog S.No, Fabric, Occasion, Care Instructions).
  - Prominent **`🛒 ADD TO CART`** and **`⚡ BUY NOW`** buttons.
- **Admin Dashboard & Excel Auto-Sync**:
  - Protected Admin login (`admin` / `admin123`).
  - Direct file upload for `stock_entry.xlsx`.
  - Automatically parses rows, extracts multiple Cloudinary image URLs, calculates MRP/discounts, and syncs to MySQL database.
  - Live inventory metrics (Total Products, Categories, Subcategories, Average Price).
  - Live MySQL database inventory table with search and filtering.
- **Shopping Cart**:
  - Real-time cart state with price calculations, total discount breakdown, and free delivery checkout.
- **AKKI User Guide (Customer Shopping Assistant & Catalog Navigator)**:
  - Floating widget pinned at the **right-bottom** corner across all pages (`🛍️ AKKI User Guide`).
  - Helps customers search available fashion products, 38+ subcategories, fabrics, and pricing.
  - Ingests customer guides and catalogs from `data/policies/` (`akki_customer_guide.pdf` & `product_catalog_guide.md`).
  - Powered by OpenAI Paid LLMs (`gpt-4o-mini`, `gpt-4o`) and embeddings (`text-embedding-3-small`).
  - Answers questions on Free Delivery, Cash on Delivery (COD), 7-day replacement assurance, and ordering steps.
  - Multi-turn conversation memory, quick-prompt FAQ chips for instant product search.
  - Dedicated FastAPI RAG endpoints: `POST /api/chat/message`, `GET /api/chat/policies`, `POST /api/chat/reindex`.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.14) |
| **Database** | MySQL 8.0 (`akki_collections_db`) |
| **Database Connector** | `mysql-connector-python` |
| **Excel Processing** | `pandas`, `openpyxl` |
| **Data Validation** | `pydantic` v2 |
| **Frontend Framework** | [Streamlit](https://streamlit.io/) with custom Flipkart CSS |
| **GenAI & RAG Engine** | OpenAI (`gpt-4o-mini`, `gpt-4o`, `text-embedding-3-small`), `pypdf`, `numpy` |
| **Server** | `uvicorn` ASGI Server |

---

## 🚀 Running the Application

### 1. Start the FastAPI Backend Server
```bash
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Start the Streamlit Frontend UI
```bash
.venv\Scripts\streamlit.exe run streamlit_app.py --server.port 8501
```
- Open in browser: [http://localhost:8501](http://localhost:8501)

---

## 🔑 Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

---

## 📂 Project Structure
```
FASTAPI_AKKI_COLLECTIONS/
│
├── config.py             # Database and app configuration
├── database.py           # MySQL connection and schema initialization
├── models.py             # Pydantic models for API requests/responses
├── excel_service.py      # Stock Excel parser & image URL extractor
├── rag_service.py        # Enterprise GenAI RAG engine for company policies
├── repository.py         # MySQL CRUD, search, filter, and upsert operations
├── main.py               # FastAPI backend with RESTful & RAG endpoints
├── streamlit_app.py      # Streamlit Flipkart-styled frontend with floating chatbot
├── .env                  # Environment variables & OpenAI API Key
├── data/
│   ├── stock_entry.xlsx  # Reference inventory spreadsheet
│   └── policies/         # Company policy documents (.pdf, .txt, .md)
│       ├── attendance_policy.pdf
│       ├── hr_policy.pdf
│       └── leave_policy.pdf
├── requirements.txt      # Python dependencies
└── README.md             # Documentation
```
