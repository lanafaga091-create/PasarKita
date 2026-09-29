# PasarKita - Marketplace untuk Security Training

PasarKita adalah marketplace e-commerce Indonesia yang dirancang khusus untuk **security training dan penetration testing** di environment lokal.

Website ini terlihat seperti marketplace sungguhan, namun memiliki beberapa kerentanan keamanan yang sengaja ditanam untuk tujuan pembelajaran.

## ⚠️ PENTING

**PasarKita hanya boleh dijalankan di environment lokal yang Anda miliki/kuasai.**

- ✅ Boleh dijalankan di laptop pribadi Anda
- ✅ Boleh dijalankan di VM lokal
- ✅ Boleh dijalankan di Docker lokal
- ❌ Jangan deploy ke internet
- ❌ Jangan gunakan data/password real
- ❌ Jangan gunakan untuk attack website orang lain

## 🚀 Quick Start

### 1. Download & Extract
Unduh file ZIP ini dan extract di folder yang Anda inginkan.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi
```bash
python app.py
```

### 4. Buka di Browser
Buka: **http://127.0.0.1:5000**

Database SQLite akan otomatis dibuat saat aplikasi dijalankan pertama kali.

## 📱 Akun Demo

Gunakan akun berikut untuk testing:

### User Biasa
- **Username:** andi
- **Password:** andi123

### User Biasa #2
- **Username:** sari
- **Password:** sari123

### Admin
- **Username:** admin
- **Password:** admin123

## 🏗️ Struktur Aplikasi

```
PasarKita/
├── app.py                    # Backend Flask (routing & API)
├── database.py              # Setup database SQLite
├── requirements.txt         # Python dependencies
│
├── index.html              # Beranda
├── login.html              # Login
├── register.html           # Register
├── product.html            # Detail produk
├── cart.html               # Keranjang
├── checkout.html           # Checkout
├── orders.html             # Pesanan saya
├── profile.html            # Profil pengguna
├── admin.html              # Admin panel
│
├── style.css               # Stylesheet
├── app.js                  # Frontend JavaScript
├── admin.js                # Admin JS (extensible)
│
├── README.md               # File ini
├── SECURITY.md             # Dokumentasi kerentanan
└── test_app.py             # Test suite
```

## 🔍 Fitur Marketplace

### Untuk User
- ✅ Browse produk
- ✅ Search & filter
- ✅ Lihat detail produk
- ✅ Review produk (dengan XSS training)
- ✅ Keranjang belanja
- ✅ Checkout (dummy)
- ✅ Kelola pesanan
- ✅ Profil pengguna
- ✅ Upload avatar

### Untuk Admin
- 📊 Dashboard
- 👥 Manajemen pengguna
- 📦 Manajemen produk
- 📋 Manajemen pesanan
- 💬 Moderasi komentar
- 🔍 Audit log

## 🎯 Security Training Content

Website ini memiliki **kerentanan keamanan yang sengaja ditanam** untuk training, meliputi:

### SQL Injection
- Endpoint `/api/products?q=` rentan terhadap SQL injection
- Database lokal yang akan di-compromise

### XSS (Cross-Site Scripting)
- Review produk tidak di-sanitize
- Field profile dapat menampilkan HTML/JavaScript

### IDOR (Insecure Direct Object Reference)
- `/api/users/<id>` tidak melakukan authorization check
- `/api/orders/<id>` dapat diakses oleh user lain

### Mass Assignment
- Endpoint `/api/profile/update` dapat menerima field `role`
- User biasa bisa upgrade diri ke admin

### Business Logic Issues
- Coupon dapat dipakai unlimited
- Quantity dapat dimanipulasi di checkout
- Stock validation lemah

### File Upload
- Upload avatar memiliki validasi yang lemah
- MIME type dapat dipalsukan

### Path Traversal
- Endpoint `/uploads/<filename>` memiliki potensi path traversal

### SSRF (Server-Side Request Forgery)
- Endpoint `/api/fetch?url=` dapat melakukan fetch terbatas

### Weak Rate Limiting
- Endpoint `/api/rate-test` tidak memiliki rate limiting

## 📖 Cara Menggunakan untuk Security Testing

### 1. Basic SQL Injection Testing
```bash
# Buka browser ke:
http://127.0.0.1:5000/
# Search dengan: ' OR '1'='1
# Atau coba injection lainnya
```

### 2. XSS Testing
```
Buka /product/1
Tambahkan review dengan:
<img src=x onerror="alert('XSS')">
atau
<script>alert('XSS')</script>
```

### 3. IDOR Testing
```
Buka URL:
http://127.0.0.1:5000/api/users/1
http://127.0.0.1:5000/api/users/2
http://127.0.0.1:5000/api/users/3
```

### 4. Mass Assignment Testing
```
POST ke /api/profile/update

Body:
{
  "email": "newemail@test.com",
  "role": "admin"
}
```

### 5. API Testing
Gunakan tools seperti:
- Burp Suite
- OWASP ZAP
- Postman
- curl

Contoh:
```bash
# Get products
curl http://127.0.0.1:5000/api/products

# Get specific user (IDOR)
curl http://127.0.0.1:5000/api/users/1

# Add to cart
curl -X POST http://127.0.0.1:5000/api/cart/add \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 999}'
```

## 📝 Testing Checklist

- [ ] SQLi pada search endpoint
- [ ] XSS pada review produk
- [ ] IDOR pada user profile & orders
- [ ] Mass assignment di profile update
- [ ] Logic bugs di checkout & coupon
- [ ] Weak file upload validation
- [ ] Path traversal di file download
- [ ] SSRF pada fetch endpoint
- [ ] Rate limiting testing
- [ ] Authorization bypass
- [ ] Session handling
- [ ] JWT token issues
- [ ] Information disclosure

Lihat `SECURITY.md` untuk detail lengkap setiap kerentanan.

## 🛠️ Konfigurasi & Environment

### Flask Debug Mode
Di production, `debug=False` sudah diatur di `app.py`.

### Database
Database SQLite (`pasar_kita.db`) akan otomatis dibuat di folder yang sama saat `app.py` dijalankan.

### Session Secret
Menggunakan secret key dummy (untuk training saja). Jangan gunakan di production.

## 🐛 Troubleshooting

### Database tidak terbuat?
```bash
# Hapus file lama jika ada
rm pasar_kita.db

# Jalankan ulang
python app.py
```

### Port 5000 sudah dipakai?
Edit `app.py` baris terakhir:
```python
app.run(host='127.0.0.1', port=8000)  # Ganti ke port lain
```

### Error import Flask?
```bash
pip install Flask==2.3.3 Werkzeug==2.3.7
```

## 📚 Resource Pembelajaran

Dokumentasi kerentanan dan cara exploitnya ada di `SECURITY.md`.

## 🤝 Kontribusi

Untuk menambah kerentanan atau fitur baru, Anda bisa:
1. Edit `app.py` untuk menambah vulnerability
2. Edit HTML files untuk UI changes
3. Edit `style.css` untuk styling

## ⚖️ Disclaimer

PasarKita dibuat untuk **tujuan pendidikan security** semata.

- Gunakan hanya di environment lokal yang Anda kuasai
- Jangan gunakan untuk menyerang sistem orang lain
- Tanggung jawab penggunaan ada di tangan user
- Developer tidak bertanggung jawab atas penggunaan yang tidak sesuai

## 📞 Support

Untuk issue atau pertanyaan:
1. Periksa dokumentasi di `SECURITY.md`
2. Review code di `app.py`
3. Check database schema di `database.py`

---

**Happy Security Testing!** 🔐

Ingat: Pengetahuan keamanan adalah untuk melindungi, bukan untuk merugikan.
