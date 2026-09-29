PasarKita - Panduan Clone & Menjalankan Aplikasi

PasarKita adalah marketplace e-commerce Indonesia yang dirancang khusus untuk security training dan penetration testing di environment lokal. Website ini terlihat seperti marketplace sungguhan, namun memiliki beberapa kerentanan keamanan yang sengaja ditanam untuk tujuan pembelajaran.

⚠️ PENTING: PasarKita hanya boleh dijalankan di environment lokal yang Anda miliki/kuasai.

· ✅ Boleh dijalankan di laptop pribadi Anda
· ✅ Boleh dijalankan di VM lokal
· ✅ Boleh dijalankan di Docker lokal
· ❌ Jangan deploy ke internet
· ❌ Jangan gunakan data/password real
· ❌ Jangan gunakan untuk attack website orang lain

---

📋 Prasyarat

Pastikan sistem Anda sudah terinstall:

Perangkat Versi Minimal Keterangan
Python 3.8+ Untuk menjalankan backend Flask
pip Terbaru Package manager Python
Git Terbaru Untuk clone repository

---

🔽 Cara Clone Repository

1. Buka Terminal / Git Bash

Buka terminal (Linux/Mac) atau Git Bash (Windows) di folder tempat Anda ingin menyimpan project.

2. Jalankan Perintah Clone

```bash
git clone https://github.com/lanafaga091-create/PasarKita.git
```

3. Masuk ke Folder Project

```bash
cd PasarKita
```

---

🚀 Cara Menjalankan Aplikasi

1. Install Dependencies

Install semua library Python yang dibutuhkan:

```bash
pip install -r requirements.txt
```

2. Jalankan Aplikasi

```bash
python app.py
```

3. Buka di Browser

Buka alamat berikut di browser Anda:

```
http://127.0.0.1:5000
```

Catatan: Database SQLite akan otomatis dibuat saat aplikasi dijalankan pertama kali.

---

👤 Akun Demo

Gunakan akun berikut untuk testing:

User Biasa

· Username: andi | Password: andi123

User Biasa #2

· Username: sari | Password: sari123

Admin

· Username: admin | Password: admin123

---

📁 Struktur Aplikasi

```
PasarKita/
├── app.py              # Backend Flask (routing & API)
├── database.py         # Setup database SQLite
├── requirements.txt    # Python dependencies
│
├── index.html          # Beranda
├── login.html          # Login
├── register.html       # Register
├── product.html        # Detail produk
├── cart.html           # Keranjang
├── checkout.html       # Checkout
├── orders.html         # Pesanan saya
├── profile.html        # Profil pengguna
├── admin.html          # Admin panel
│
├── style.css           # Stylesheet
├── app.js              # Frontend JavaScript
├── admin.js            # Admin JS (extensible)
│
├── README.md           # File ini
├── SECURITY.md         # Dokumentasi kerentanan
└── test_app.py         # Test suite
```[reference:4]

---

## ✨ Fitur Marketplace

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
- Dashboard
- Manajemen pengguna
- Manajemen produk
- Manajemen pesanan
- Moderasi komentar
- Audit log[reference:5]

---

## 🔒 Security Training Content

Website ini memiliki **kerentanan keamanan yang sengaja ditanam** untuk training, meliputi:

### SQL Injection
- Endpoint `/api/products?q=` rentan terhadap SQL injection

### XSS (Cross-Site Scripting)
- Review produk tidak di-sanitize
- Field profile dapat menampilkan HTML/JavaScript

### IDOR (Insecure Direct Object Reference)
- `/api/users/` tidak melakukan authorization check
- `/api/orders/` dapat diakses oleh user lain

### Mass Assignment
- Endpoint `/api/profile/update` dapat menerima field `role`

### Business Logic Issues
- Coupon dapat dipakai unlimited
- Quantity dapat dimanipulasi di checkout
- Stock validation lemah

### File Upload
- Upload avatar memiliki validasi yang lemah
- MIME type dapat dipalsukan

### Path Traversal
- Endpoint `/uploads/` memiliki potensi path traversal

### SSRF (Server-Side Request Forgery)
- Endpoint `/api/fetch?url=` dapat melakukan fetch[reference:6]

---

## ❓ Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `python: command not found` | Install Python dari python.org |
| `pip: command not found` | Jalankan `python -m ensurepip` |
| Port 5000 sudah digunakan | Ubah port di `app.py` atau matikan aplikasi lain |
| Module not found | Jalankan ulang `pip install -r requirements.txt` |

---

## 📄 Lisensi

Project ini dibuat untuk tujuan edukasi security training. Gunakan dengan bijak dan hanya di environment lokal yang Anda kuasai.
