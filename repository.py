import json
from typing import List, Optional, Dict, Any, Tuple
from database import get_connection

def serialize_images(image_urls: List[str]) -> str:
    return json.dumps(image_urls if image_urls else [])

def deserialize_images(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    # fallback to comma/newline split
    return [u.strip() for u in str(raw).split(",") if u.strip()]

def row_to_product(row: dict) -> dict:
    if not row:
        return {}
    product = dict(row)
    product["image_urls"] = deserialize_images(product.get("image_urls"))
    if "created_at" in product and product["created_at"]:
        product["created_at"] = str(product["created_at"])
    if "updated_at" in product and product["updated_at"]:
        product["updated_at"] = str(product["updated_at"])
    if "price" in product:
        product["price"] = float(product["price"])
    if "mrp" in product:
        product["mrp"] = float(product["mrp"])
    if "rating" in product:
        product["rating"] = float(product["rating"])
    return product

def get_categories_summary() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT category, subcategory, COUNT(*) as cnt
        FROM products
        GROUP BY category, subcategory
        ORDER BY category ASC, subcategory ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        categories_dict = {}
        for r in rows:
            cat = r["category"]
            sub = r["subcategory"]
            cnt = r["cnt"]
            if cat not in categories_dict:
                categories_dict[cat] = {
                    "category": cat,
                    "count": 0,
                    "subcategories": []
                }
            categories_dict[cat]["count"] += cnt
            if sub not in categories_dict[cat]["subcategories"]:
                categories_dict[cat]["subcategories"].append(sub)
                
        return list(categories_dict.values())
    finally:
        conn.close()

def get_subcategories(category: Optional[str] = None) -> List[str]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if category and category != "All":
            cursor.execute("SELECT DISTINCT subcategory FROM products WHERE category = %s ORDER BY subcategory ASC", (category,))
        else:
            cursor.execute("SELECT DISTINCT subcategory FROM products ORDER BY subcategory ASC")
        return [r[0] for r in cursor.fetchall() if r[0]]
    finally:
        conn.close()

def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = None,
    limit: int = 200,
    offset: int = 0
) -> List[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conditions = []
        params = []

        if category and category.lower() != "all":
            conditions.append("category = %s")
            params.append(category)

        if subcategory and subcategory.lower() != "all":
            conditions.append("subcategory = %s")
            params.append(subcategory)

        if search and search.strip():
            kw = f"%{search.strip()}%"
            conditions.append("(title LIKE %s OR description LIKE %s OR category LIKE %s OR subcategory LIKE %s)")
            params.extend([kw, kw, kw, kw])

        if min_price is not None:
            conditions.append("price >= %s")
            params.append(min_price)

        if max_price is not None:
            conditions.append("price <= %s")
            params.append(max_price)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        order_clause = " ORDER BY CASE WHEN sno IS NULL THEN 1 ELSE 0 END, sno ASC, id ASC"
        if sort_by == "price_asc":
            order_clause = " ORDER BY price ASC"
        elif sort_by == "price_desc":
            order_clause = " ORDER BY price DESC"
        elif sort_by == "rating_desc":
            order_clause = " ORDER BY rating DESC"
        elif sort_by == "discount_desc":
            order_clause = " ORDER BY discount_pct DESC"
        elif sort_by == "newest":
            order_clause = " ORDER BY id DESC"

        query = f"SELECT * FROM products {where_clause} {order_clause} LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [row_to_product(r) for r in rows]
    finally:
        conn.close()

def get_product_by_id(product_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        return row_to_product(row) if row else None
    finally:
        conn.close()

def bulk_upsert_products(product_list: List[dict], sync_mode: bool = False) -> Tuple[int, int]:
    """
    Upserts a list of product dictionaries into the database.
    If sync_mode is True, table is cleared and repopulated strictly from the uploaded list.
    """
    conn = get_connection()
    inserted = 0
    updated = 0
    try:
        cursor = conn.cursor(dictionary=True)
        if sync_mode:
            cursor.execute("TRUNCATE TABLE products")
            for item in product_list:
                img_json = serialize_images(item.get("image_urls", []))
                primary_img = item.get("primary_image")
                if not primary_img and item.get("image_urls"):
                    primary_img = item["image_urls"][0]

                insert_sql = """
                INSERT INTO products (
                    sno, category, subcategory, title, description,
                    price, mrp, discount_pct, rating, reviews_count,
                    image_urls, primary_image, stock_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    item.get("sno"),
                    item.get("category"),
                    item.get("subcategory"),
                    item.get("title"),
                    item.get("description"),
                    item.get("price"),
                    item.get("mrp"),
                    item.get("discount_pct", 0),
                    item.get("rating", 4.3),
                    item.get("reviews_count", 120),
                    img_json,
                    primary_img,
                    item.get("stock_status", "In Stock")
                ))
                inserted += 1

            conn.commit()
            return inserted, 0

        for item in product_list:
            sno = item.get("sno")
            # If sno is present, match strictly by sno to prevent different products with the same title from overwriting
            existing = None
            if sno is not None:
                cursor.execute("SELECT id FROM products WHERE sno = %s", (sno,))
                existing = cursor.fetchone()
            elif item.get("title") and item.get("category"):
                cursor.execute("SELECT id FROM products WHERE title = %s AND category = %s", (item["title"], item["category"]))
                existing = cursor.fetchone()

            img_json = serialize_images(item.get("image_urls", []))
            primary_img = item.get("primary_image")
            if not primary_img and item.get("image_urls"):
                primary_img = item["image_urls"][0]

            if existing:
                update_sql = """
                UPDATE products SET
                    sno = %s, category = %s, subcategory = %s, title = %s,
                    description = %s, price = %s, mrp = %s, discount_pct = %s,
                    rating = %s, reviews_count = %s, image_urls = %s,
                    primary_image = %s, stock_status = %s
                WHERE id = %s
                """
                cursor.execute(update_sql, (
                    item.get("sno"),
                    item.get("category"),
                    item.get("subcategory"),
                    item.get("title"),
                    item.get("description"),
                    item.get("price"),
                    item.get("mrp"),
                    item.get("discount_pct", 0),
                    item.get("rating", 4.3),
                    item.get("reviews_count", 120),
                    img_json,
                    primary_img,
                    item.get("stock_status", "In Stock"),
                    existing["id"]
                ))
                updated += 1
            else:
                insert_sql = """
                INSERT INTO products (
                    sno, category, subcategory, title, description,
                    price, mrp, discount_pct, rating, reviews_count,
                    image_urls, primary_image, stock_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    item.get("sno"),
                    item.get("category"),
                    item.get("subcategory"),
                    item.get("title"),
                    item.get("description"),
                    item.get("price"),
                    item.get("mrp"),
                    item.get("discount_pct", 0),
                    item.get("rating", 4.3),
                    item.get("reviews_count", 120),
                    img_json,
                    primary_img,
                    item.get("stock_status", "In Stock")
                ))
                inserted += 1

        conn.commit()
        return inserted, updated
    finally:
        conn.close()

def delete_product(product_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_stats() -> dict:
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total_products FROM products")
        total_p = cursor.fetchone()["total_products"]
        
        cursor.execute("SELECT COUNT(DISTINCT category) as total_categories FROM products")
        total_c = cursor.fetchone()["total_categories"]
        
        cursor.execute("SELECT COUNT(DISTINCT subcategory) as total_subcategories FROM products")
        total_s = cursor.fetchone()["total_subcategories"]
        
        cursor.execute("SELECT AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price FROM products")
        price_stats = cursor.fetchone()

        return {
            "total_products": total_p,
            "total_categories": total_c,
            "total_subcategories": total_s,
            "avg_price": round(price_stats["avg_price"] or 0, 2),
            "min_price": float(price_stats["min_price"] or 0),
            "max_price": float(price_stats["max_price"] or 0)
        }
    finally:
        conn.close()
