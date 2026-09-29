import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse

from flask import (Flask, render_template_string, request, jsonify, 
                   session, redirect, url_for, send_file, g)
from werkzeug.utils import secure_filename

from database import init_db, get_db, dict_from_row

app = Flask(__name__)
app.secret_key = 'super-secret-key-not-for-production'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# ============= HELPER FUNCTIONS =============

def load_html_file(filename):
    """Load HTML file dari root directory"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"<h1>Error: {filename} not found</h1>"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        g.user_id = session['user_id']
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        
        db = get_db()
        user = db.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()
        
        if user is None or user['role'] != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        g.user_id = session['user_id']
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def log_audit(action, details='', user_id=None):
    """Log audit trail"""
    db = get_db()
    db.execute('''INSERT INTO audit_logs (user_id, action, details, ip_address)
                  VALUES (?, ?, ?, ?)''',
               (user_id, action, details, request.remote_addr))
    db.commit()
    db.close()

# ============= PAGE ROUTES =============

@app.route('/')
def index():
    html = load_html_file('index.html')
    return render_template_string(html)

@app.route('/login')
def login_page():
    html = load_html_file('login.html')
    return render_template_string(html)

@app.route('/register')
def register_page():
    html = load_html_file('register.html')
    return render_template_string(html)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    html = load_html_file('product.html')
    return render_template_string(html, product_id=product_id)

@app.route('/cart')
@login_required
def cart_page():
    html = load_html_file('cart.html')
    return render_template_string(html)

@app.route('/checkout')
@login_required
def checkout_page():
    html = load_html_file('checkout.html')
    return render_template_string(html)

@app.route('/orders')
@login_required
def orders_page():
    html = load_html_file('orders.html')
    return render_template_string(html)

@app.route('/profile')
@login_required
def profile_page():
    html = load_html_file('profile.html')
    return render_template_string(html)

@app.route('/admin')
@admin_required
def admin_page():
    html = load_html_file('admin.html')
    return render_template_string(html)

# ============= API ROUTES - AUTH =============

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register user - Simple implementation"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields required'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Password minimum 4 karakter'}), 400
    
    db = get_db()
    
    # Check if user exists - VULNERABLE: Simple query check
    existing = db.execute('SELECT id FROM users WHERE username = ? OR email = ?',
                         (username, email)).fetchone()
    
    if existing:
        db.close()
        return jsonify({'error': 'Username atau email sudah terdaftar'}), 400
    
    hashed_pwd = hash_password(password)
    
    try:
        db.execute('''INSERT INTO users (username, email, password, role)
                      VALUES (?, ?, ?, ?)''',
                   (username, email, hashed_pwd, 'user'))
        db.commit()
        log_audit('USER_REGISTERED', f'Username: {username}')
    except Exception as e:
        db.close()
        return jsonify({'error': 'Registration failed'}), 400
    
    db.close()
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username dan password diperlukan'}), 400
    
    db = get_db()
    user = db.execute('SELECT id, username, role, password FROM users WHERE username = ?',
                     (username,)).fetchone()
    db.close()
    
    if user is None:
        return jsonify({'error': 'Username tidak ditemukan'}), 401
    
    if user['password'] != hash_password(password):
        return jsonify({'error': 'Password salah'}), 401
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    
    log_audit('USER_LOGIN', f'Username: {username}', user['id'])
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    if 'user_id' in session:
        log_audit('USER_LOGOUT', '', session['user_id'])
    
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/auth/token', methods=['POST'])
def api_token():
    """Generate JWT-like token (dummy implementation)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    # Create simple JWT-like token (not real JWT)
    payload = f"{user_id}.{secrets.token_hex(16)}"
    token = payload
    
    return jsonify({
        'token': token,
        'expires_in': 3600,
        'user_id': user_id
    }), 200

# ============= API ROUTES - PRODUCTS =============

@app.route('/api/products')
def api_products():
    """Get all products or filtered - VULNERABLE: SQL Injection"""
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'name')
    
    db = get_db()
    query = 'SELECT * FROM products WHERE 1=1'
    params = []
    
    # VULNERABLE: SQL Injection dalam search parameter
    if search:
        # Build query dengan string concatenation (VULNERABLE)
        query += f" AND (name LIKE '%{search}%' OR description LIKE '%{search}%')"
    
    if category and category.isdigit():
        query += ' AND category_id = ?'
        params.append(int(category))
    
    # VULNERABLE: Sort injection - tidak divalidasi
    if sort in ['name', 'price', 'rating']:
        query += f' ORDER BY {sort}'
    
    try:
        products = db.execute(query, params).fetchall()
        db.close()
        
        result = [dict(p) for p in products]
        return jsonify(result), 200
    except Exception as e:
        db.close()
        # VULNERABLE: Information disclosure - reveal database error
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/products/<int:product_id>')
def api_product_detail(product_id):
    """Get product detail - VULNERABLE: IDOR possible"""
    db = get_db()
    
    # Simple IDOR: ID tidak divalidasi secara proper
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if product is None:
        db.close()
        return jsonify({'error': 'Product not found'}), 404
    
    # Get comments - VULNERABLE: XSS di comments
    comments = db.execute(
        'SELECT c.id, c.rating, c.comment, u.username, c.created_at FROM comments c '
        'JOIN users u ON c.user_id = u.id WHERE c.product_id = ? ORDER BY c.created_at DESC',
        (product_id,)
    ).fetchall()
    
    db.close()
    
    result = dict(product)
    result['comments'] = [dict(c) for c in comments]
    
    return jsonify(result), 200

# ============= API ROUTES - USERS =============

@app.route('/api/users/<int:user_id>')
def api_user_detail(user_id):
    """Get user profile - VULNERABLE: IDOR"""
    db = get_db()
    
    # VULNERABLE IDOR: Tidak ada validasi authorization
    user = db.execute(
        'SELECT id, username, email, full_name, phone, address, city, postal_code, created_at '
        'FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    
    db.close()
    
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(dict(user)), 200

@app.route('/api/profile', methods=['GET'])
@login_required
def api_profile():
    """Get current user profile"""
    db = get_db()
    user = db.execute(
        'SELECT id, username, email, full_name, phone, address, city, postal_code, avatar '
        'FROM users WHERE id = ?',
        (g.user_id,)
    ).fetchone()
    db.close()
    
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(dict(user)), 200

@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_profile_update():
    """Update user profile - VULNERABLE: Mass Assignment"""
    data = request.get_json()
    
    db = get_db()
    
    # VULNERABLE: Mass Assignment - bisa update field yang tidak seharusnya
    # Contoh: bisa ubah 'role' ke 'admin'
    updatable_fields = ['full_name', 'email', 'phone', 'address', 'city', 'postal_code']
    
    # Jika ada field 'role' di request, seharusnya ditolak tapi tidak
    if 'role' in data:
        # Update role jika user mengirimnya (VULNERABLE)
        db.execute('UPDATE users SET role = ? WHERE id = ?', 
                   (data['role'], g.user_id))
    
    # Update normal fields
    for field in updatable_fields:
        if field in data:
            db.execute(f'UPDATE users SET {field} = ? WHERE id = ?',
                      (data[field], g.user_id))
    
    db.commit()
    log_audit('PROFILE_UPDATED', '', g.user_id)
    db.close()
    
    return jsonify({'message': 'Profile updated'}), 200

# ============= API ROUTES - CART =============

@app.route('/api/cart', methods=['GET'])
@login_required
def api_get_cart():
    """Get cart items"""
    db = get_db()
    cart_items = db.execute(
        'SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.stock '
        'FROM cart c JOIN products p ON c.product_id = p.id '
        'WHERE c.user_id = ?',
        (g.user_id,)
    ).fetchall()
    db.close()
    
    items = [dict(item) for item in cart_items]
    return jsonify(items), 200

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_cart_add():
    """Add product to cart"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id or quantity < 1:
        return jsonify({'error': 'Invalid input'}), 400
    
    db = get_db()
    
    # Check product exists and stock
    product = db.execute('SELECT price, stock FROM products WHERE id = ?',
                        (product_id,)).fetchone()
    
    if product is None:
        db.close()
        return jsonify({'error': 'Product not found'}), 404
    
    # VULNERABLE: No proper stock validation
    if quantity > product['stock']:
        quantity = product['stock']
    
    # Add to cart
    existing = db.execute(
        'SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?',
        (g.user_id, product_id)
    ).fetchone()
    
    if existing:
        db.execute('UPDATE cart SET quantity = quantity + ? WHERE id = ?',
                  (quantity, existing['id']))
    else:
        db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
                  (g.user_id, product_id, quantity))
    
    db.commit()
    db.close()
    
    return jsonify({'message': 'Product added to cart'}), 201

@app.route('/api/cart/remove', methods=['POST'])
@login_required
def api_cart_remove():
    """Remove from cart"""
    data = request.get_json()
    cart_id = data.get('cart_id')
    
    db = get_db()
    
    # Simple removal - VULNERABLE: IDOR possible
    db.execute('DELETE FROM cart WHERE id = ?', (cart_id,))
    
    db.commit()
    db.close()
    
    return jsonify({'message': 'Removed from cart'}), 200

# ============= API ROUTES - CHECKOUT & ORDERS =============

@app.route('/api/checkout', methods=['POST'])
@login_required
def api_checkout():
    """Checkout - VULNERABLE: Business Logic"""
    data = request.get_json()
    coupon_code = data.get('coupon_code', '').strip().upper()
    
    db = get_db()
    
    # Get cart items
    cart_items = db.execute(
        'SELECT c.product_id, c.quantity, p.price FROM cart c '
        'JOIN products p ON c.product_id = p.id WHERE c.user_id = ?',
        (g.user_id,)
    ).fetchall()
    
    if not cart_items:
        db.close()
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate total - VULNERABLE: Client dapat manipulasi
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    discount = 0
    
    # Coupon validation - VULNERABLE: Multiple issues
    if coupon_code:
        coupon = db.execute(
            'SELECT id, discount_percent, is_active FROM coupons WHERE code = ?',
            (coupon_code,)
        ).fetchone()
        
        if coupon and coupon['is_active']:
            discount = total * (coupon['discount_percent'] / 100)
            # VULNERABLE: Coupon dapat dipakai unlimited times
            # Tidak ada validasi max_uses
    
    final_price = max(total - discount, 0)
    
    # VULNERABLE: Quantity tidak divalidasi ulang
    # VULNERABLE: Stock tidak dicheck saat checkout
    
    # Create order
    db.execute('''INSERT INTO orders (user_id, total_price, status, coupon_code, discount)
                  VALUES (?, ?, ?, ?, ?)''',
               (g.user_id, final_price, 'Pending', coupon_code, discount))
    
    order = db.execute(
        'SELECT id FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (g.user_id,)
    ).fetchone()
    
    # Add order items
    for item in cart_items:
        db.execute('''INSERT INTO order_items (order_id, product_id, quantity, price)
                      VALUES (?, ?, ?, ?)''',
                   (order['id'], item['product_id'], item['quantity'], item['price']))
        
        # Update stock - VULNERABLE: Race condition possible
        db.execute('UPDATE products SET stock = stock - ? WHERE id = ?',
                  (item['quantity'], item['product_id']))
    
    # Clear cart
    db.execute('DELETE FROM cart WHERE user_id = ?', (g.user_id,))
    
    db.commit()
    log_audit('CHECKOUT_COMPLETED', f'Order ID: {order["id"]}', g.user_id)
    db.close()
    
    return jsonify({
        'message': 'Order created successfully',
        'order_id': order['id'],
        'total': final_price,
        'discount': discount
    }), 201

@app.route('/api/orders')
@login_required
def api_get_orders():
    """Get user orders"""
    db = get_db()
    orders = db.execute(
        'SELECT id, total_price, status, coupon_code, discount, created_at FROM orders '
        'WHERE user_id = ? ORDER BY created_at DESC',
        (g.user_id,)
    ).fetchall()
    db.close()
    
    return jsonify([dict(o) for o in orders]), 200

@app.route('/api/orders/<int:order_id>')
@login_required
def api_order_detail(order_id):
    """Get order detail - VULNERABLE: IDOR"""
    db = get_db()
    
    # VULNERABLE IDOR: Tidak ada pengecekan ownership
    order = db.execute(
        'SELECT id, user_id, total_price, status, created_at FROM orders WHERE id = ?',
        (order_id,)
    ).fetchone()
    
    if order is None:
        db.close()
        return jsonify({'error': 'Order not found'}), 404
    
    # Get order items
    items = db.execute(
        'SELECT product_id, quantity, price FROM order_items WHERE order_id = ?',
        (order_id,)
    ).fetchall()
    
    db.close()
    
    result = dict(order)
    result['items'] = [dict(i) for i in items]
    
    return jsonify(result), 200

# ============= API ROUTES - COMMENTS =============

@app.route('/api/comments/add', methods=['POST'])
@login_required
def api_add_comment():
    """Add product review - VULNERABLE: XSS"""
    data = request.get_json()
    product_id = data.get('product_id')
    rating = data.get('rating', 5)
    comment = data.get('comment', '').strip()
    
    if not product_id or not comment:
        return jsonify({'error': 'Missing fields'}), 400
    
    if rating < 1 or rating > 5:
        rating = 5
    
    db = get_db()
    
    # VULNERABLE: XSS - Comment tidak di-sanitize
    # HTML tags akan disimpan dan ditampilkan
    db.execute('''INSERT INTO comments (product_id, user_id, rating, comment)
                  VALUES (?, ?, ?, ?)''',
               (product_id, g.user_id, rating, comment))
    
    db.commit()
    log_audit('COMMENT_ADDED', f'Product: {product_id}', g.user_id)
    db.close()
    
    return jsonify({'message': 'Comment added'}), 201

# ============= API ROUTES - UPLOAD =============

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """Upload file - VULNERABLE: File upload issues"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # VULNERABLE: Extension check tidak sufficient
    filename = secure_filename(file.filename)
    
    # VULNERABLE: MIME type dapat dipalsukan
    if file.content_type not in ['image/png', 'image/jpeg', 'image/gif']:
        # Bisa bypass dengan content-type palsu
        pass
    
    # VULNERABLE: Filename tidak di-validate properly
    # Path traversal mungkin terjadi
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({
        'message': 'File uploaded',
        'filename': filename,
        'url': f'/uploads/{filename}'
    }), 201

@app.route('/uploads/<path:filename>')
def download_file(filename):
    """Download uploaded file - VULNERABLE: Path traversal"""
    # VULNERABLE: Path traversal
    # User bisa request: /uploads/../../../../etc/passwd
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        return send_file(filepath)
    
    return jsonify({'error': 'File not found'}), 404

# ============= API ROUTES - FETCH (SSRF Simulation) =============

@app.route('/api/fetch', methods=['GET'])
def api_fetch():
    """Fetch data - VULNERABLE: SSRF (controlled)"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL parameter required'}), 400
    
    # VULNERABLE: SSRF dengan pembatasan
    # Hanya boleh akses internal service dummy
    parsed = urlparse(url)
    host = parsed.netloc.split(':')[0]
    
    # Whitelist internal services
    internal_services = ['internal-service', 'localhost', '127.0.0.1']
    
    if host not in internal_services:
        # Bisa bypass dengan cara tertentu
        return jsonify({'error': 'Service unavailable'}), 403
    
    # Simulated internal service response
    if host in internal_services:
        return jsonify({
            'status': 'OK',
            'data': 'Internal service response (dummy)'
        }), 200
    
    return jsonify({'error': 'Connection failed'}), 500

# ============= API ROUTES - RATE LIMITING =============

@app.route('/api/rate-test', methods=['POST', 'GET'])
def api_rate_test():
    """Test rate limiting - VULNERABLE: Weak rate limiting"""
    # No actual rate limiting implemented
    # Just returns success every time
    
    return jsonify({
        'status': 'success',
        'message': 'Request processed',
        'timestamp': datetime.now().isoformat()
    }), 200

# ============= API ROUTES - ADMIN =============

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def api_admin_users():
    """Get all users (admin only)"""
    db = get_db()
    users = db.execute(
        'SELECT id, username, email, role, created_at FROM users'
    ).fetchall()
    db.close()
    
    return jsonify([dict(u) for u in users]), 200

@app.route('/api/admin/products', methods=['GET'])
@admin_required
def api_admin_products():
    """Get all products (admin only)"""
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    db.close()
    
    return jsonify([dict(p) for p in products]), 200

@app.route('/api/admin/orders', methods=['GET'])
@admin_required
def api_admin_orders():
    """Get all orders (admin only)"""
    db = get_db()
    orders = db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    db.close()
    
    return jsonify([dict(o) for o in orders]), 200

@app.route('/api/admin/audit', methods=['GET'])
@admin_required
def api_admin_audit():
    """Get audit logs (admin only)"""
    db = get_db()
    logs = db.execute('SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100').fetchall()
    db.close()
    
    return jsonify([dict(l) for l in logs]), 200

# ============= INITIALIZATION =============

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='127.0.0.1', port=5000)
