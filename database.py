import mysql.connector
from mysql.connector import pooling
import logging
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

logger = logging.getLogger("akki_backend.db")

def ensure_database_exists():
    """Ensure the target database exists in MySQL."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error ensuring database exists: {e}")
        raise e

def get_connection():
    """Returns a direct connection to MySQL database."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

def init_db():
    """Creates the necessary tables if they do not exist."""
    ensure_database_exists()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sno INT,
            category VARCHAR(100) NOT NULL,
            subcategory VARCHAR(100) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            mrp DECIMAL(10, 2) NOT NULL,
            discount_pct INT DEFAULT 0,
            rating DECIMAL(2, 1) DEFAULT 4.3,
            reviews_count INT DEFAULT 128,
            image_urls LONGTEXT NOT NULL,
            primary_image VARCHAR(1000),
            stock_status VARCHAR(50) DEFAULT 'In Stock',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_category (category),
            INDEX idx_subcategory (subcategory),
            INDEX idx_title (title)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
    finally:
        conn.close()
