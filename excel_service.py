import io
import re
import pandas as pd
from typing import List, Dict, Any

def clean_image_urls(raw_urls: Any) -> List[str]:
    """Extract and clean a list of image URLs from raw cell string."""
    if not raw_urls or pd.isna(raw_urls):
        return []
    
    text = str(raw_urls).strip()
    # Split by comma or newlines or semicolons
    parts = re.split(r'[\r\n,;]+', text)
    cleaned = []
    for p in parts:
        url = p.strip()
        if url.startswith("http://") or url.startswith("https://"):
            cleaned.append(url)
    return cleaned

def parse_stock_excel(file_bytes_or_path) -> List[Dict[str, Any]]:
    """
    Parses a stock_entry Excel spreadsheet and returns a list of cleaned product dicts.
    Accepts file path string or bytes buffer.
    """
    df = pd.read_excel(file_bytes_or_path)
    
    # Normalize column names: lowercase and stripped of special chars/spaces
    col_map = {}
    for col in df.columns:
        norm = str(col).strip().lower().replace("_", "").replace(" ", "")
        col_map[norm] = col

    def get_val(row, *candidates, default=""):
        for cand in candidates:
            norm_cand = cand.lower().replace("_", "").replace(" ", "")
            if norm_cand in col_map:
                actual_col = col_map[norm_cand]
                val = row.get(actual_col)
                if pd.notna(val):
                    return val
        return default

    products = []
    for idx, row in df.iterrows():
        category = str(get_val(row, "category", default="Uncategorized")).strip()
        subcategory = str(get_val(row, "subcategory", "sub_category", default="General")).strip()
        title = str(get_val(row, "title", "product_name", "name", default=f"Product {idx+1}")).strip()
        description = str(get_val(row, "description", "desc", default="")).strip()
        
        # Price parsing
        price_raw = get_val(row, "price", "selling_price", default=0)
        try:
            # clean currency symbols, commas
            cleaned_price_str = re.sub(r'[^\d.]', '', str(price_raw))
            price = float(cleaned_price_str) if cleaned_price_str else 0.0
        except Exception:
            price = 0.0

        sno_raw = get_val(row, "sno", "s_no", "id", default=idx+1)
        try:
            sno = int(float(str(sno_raw).strip()))
        except Exception:
            sno = idx + 1

        raw_images = get_val(row, "imageUrls", "image_urls", "images", "image", default="")
        image_list = clean_image_urls(raw_images)
        primary_image = image_list[0] if image_list else "https://res.cloudinary.com/dh96id3hk/image/upload/v1757262322/146691a5-d2a3-4bf8-9835-afa771aa532f_vcxodf.jpg"

        # Calculate MRP and discount for Flipkart-like display
        # Default ~35-50% discount markup
        if price > 0:
            mrp = round(price * 1.55, -1) # rounded to nearest 10
            if mrp <= price:
                mrp = round(price * 1.4)
            discount_pct = int(round(((mrp - price) / mrp) * 100))
        else:
            mrp = price
            discount_pct = 0

        # Deterministic appealing rating based on title/sno
        rating = round(4.1 + ((sno * 7) % 8) * 0.1, 1)
        if rating > 4.9:
            rating = 4.8
        reviews_count = 45 + ((sno * 37) % 350)

        products.append({
            "sno": sno,
            "category": category,
            "subcategory": subcategory,
            "title": title,
            "description": description,
            "price": price,
            "mrp": mrp,
            "discount_pct": discount_pct,
            "rating": rating,
            "reviews_count": reviews_count,
            "image_urls": image_list,
            "primary_image": primary_image,
            "stock_status": "In Stock"
        })

    return products
