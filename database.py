import sqlite3
import os
from datetime import datetime

DB_FILE = 'pasar_kita.db'

def init_db():
    """Initialize database dengan schema dan dummy data"""
    if os.path.exists(DB_FILE):
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        avatar TEXT DEFAULT '/default-avatar.svg',
        full_name TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        address TEXT DEFAULT '',
        city TEXT DEFAULT '',
        postal_code TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Categories table
    c.execute('''CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT DEFAULT '',
        icon TEXT DEFAULT '📦'
    )''')
    
    # Products table
    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        category_id INTEGER NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        image TEXT DEFAULT '/product.svg',
        seller_id INTEGER DEFAULT 1,
        rating REAL DEFAULT 5.0,
        total_reviews INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id),
        FOREIGN KEY (seller_id) REFERENCES users(id)
    )''')
    
    # Reviews/Comments table
    c.execute('''CREATE TABLE comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER DEFAULT 5,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Cart table
    c.execute('''CREATE TABLE cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    
    # Orders table
    c.execute('''CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'Pending',
        coupon_code TEXT DEFAULT '',
        discount REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Order Items table
    c.execute('''CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    
    # Coupons table
    c.execute('''CREATE TABLE coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_percent REAL NOT NULL,
        max_uses INTEGER DEFAULT -1,
        uses INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1
    )''')
    
    # Notifications table
    c.execute('''CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Sessions table
    c.execute('''CREATE TABLE sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_token TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # API Keys dummy table
    c.execute('''CREATE TABLE api_keys_dummy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        api_key TEXT UNIQUE NOT NULL,
        name TEXT DEFAULT 'API Key',
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Audit Logs table
    c.execute('''CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT DEFAULT '',
        ip_address TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Password Reset Tokens table
    c.execute('''CREATE TABLE password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP,
        used BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Insert dummy users
    users = [
        ('andi', 'andi@pasar.test', 'andi123', 'user', 'Andi Wijaya'),
        ('sari', 'sari@pasar.test', 'sari123', 'user', 'Sari Kusuma'),
        ('admin', 'admin@pasar.test', 'admin123', 'admin', 'Admin PasarKita'),
    ]
    
    for username, email, password, role, full_name in users:
        c.execute('''INSERT INTO users (username, email, password, role, full_name)
                     VALUES (?, ?, ?, ?, ?)''',
                  (username, email, password, role, full_name))
    
    # Insert categories
    categories = [
        ('Elektronik', 'Gadget dan perangkat elektronik', '📱'),
        ('Fashion', 'Pakaian dan aksesoris', '👕'),
        ('Rumah & Dapur', 'Peralatan rumah tangga', '🏠'),
        ('Olahraga', 'Perlengkapan olahraga', '⚽'),
        ('Buku', 'Buku dan literatur', '📚'),
    ]
    
    for name, desc, icon in categories:
        c.execute('''INSERT INTO categories (name, description, icon)
                     VALUES (?, ?, ?)''',
                  (name, desc, icon))
    
    # Insert dummy products
    products = [
        ('Smartphone Android 64GB', 'Smartphone dengan spesifikasi gaming, RAM 8GB, prosesor terbaru', 1, 2500000, 15),
        ('Laptop Gaming RTX 3060', 'Laptop gaming 15 inch dengan RTX 3060, i7-11700H, 16GB RAM', 1, 12000000, 5),
        ('Wireless Earbuds Pro', 'Earbuds dengan noise cancellation, baterai 30 jam', 1, 850000, 42),
        ('T-Shirt Cotton Premium', 'Kaos 100% cotton, tersedia berbagai warna dan ukuran', 2, 75000, 100),
        ('Sepatu Olahraga Running', 'Sepatu running nyaman dengan teknologi cushioning terbaru', 2, 450000, 28),
        ('Set Peralatan Dapur', 'Panci, wajan, dan pisau berkualitas tinggi 12 pcs', 3, 320000, 12),
        ('Rice Cooker 3L', 'Rice cooker modern dengan timer digital', 3, 180000, 8),
        ('Dumbbell Set 20kg', 'Dumbbell adjustable dengan stand, cocok untuk fitness rumahan', 4, 250000, 6),
        ('Buku Python Programming', 'Panduan lengkap Python dari dasar hingga advanced', 5, 120000, 25),
        ('Buku Cybersecurity Basics', 'Pengenalan dasar keamanan siber dan penetration testing', 5, 150000, 18),
    ]
    
    for name, desc, cat_id, price, stock in products:
        c.execute('''INSERT INTO products (name, description, category_id, price, stock)
                     VALUES (?, ?, ?, ?, ?)''',
                  (name, desc, cat_id, price, stock))
    
    # Insert coupons
    coupons = [
        ('WELCOME10', 10),
        ('WELCOME25', 25),
        ('WELCOME50', 50),
    ]
    
    for code, discount in coupons:
        c.execute('''INSERT INTO coupons (code, discount_percent, max_uses, is_active)
                     VALUES (?, ?, ?, ?)''',
                  (code, discount, -1, 1))
    
    # Insert sample comments
    c.execute('''INSERT INTO comments (product_id, user_id, rating, comment)
                 VALUES (?, ?, ?, ?)''',
              (1, 2, 5, '<b>Sangat bagus!</b> Produk sesuai deskripsi dan cepat sampai.'))
    
    c.execute('''INSERT INTO comments (product_id, user_id, rating, comment)
                 VALUES (?, ?, ?, ?)''',
              (1, 2, 4, 'Bagus tapi baterai cepat habis'))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """Convert sqlite3.Row to dict"""
    if row is None:
        return None
    return dict(row)
