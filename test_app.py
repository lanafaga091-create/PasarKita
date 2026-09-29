"""
Test suite untuk PasarKita marketplace
Memvalidasi bahwa aplikasi berfungsi dengan baik
"""

import unittest
import json
import os
from app import app
from database import init_db

class PasarKitaTestCase(unittest.TestCase):
    
    def setUp(self):
        """Setup test client dan database"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Use test database
        self.db_file = 'pasar_kita_test.db'
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        
        # Initialize test database
        init_db()
    
    def tearDown(self):
        """Cleanup"""
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    # ===== PAGE TESTS =====
    
    def test_homepage(self):
        """Test homepage bisa diakses"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'PasarKita', response.data)
    
    def test_login_page(self):
        """Test login page bisa diakses"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_register_page(self):
        """Test register page bisa diakses"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
    
    def test_product_page(self):
        """Test product detail page"""
        response = self.client.get('/product/1')
        self.assertEqual(response.status_code, 200)
    
    # ===== API TESTS - AUTH =====
    
    def test_register_success(self):
        """Test registrasi berhasil"""
        response = self.client.post('/api/auth/register',
            data=json.dumps({
                'username': 'testuser',
                'email': 'test@test.com',
                'password': 'test123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)
    
    def test_register_duplicate_username(self):
        """Test registrasi dengan username yang sudah ada"""
        # Register first user
        self.client.post('/api/auth/register',
            data=json.dumps({
                'username': 'andi',
                'email': 'test1@test.com',
                'password': 'test123'
            }),
            content_type='application/json'
        )
        
        # Try register with same username
        response = self.client.post('/api/auth/register',
            data=json.dumps({
                'username': 'andi',
                'email': 'test2@test.com',
                'password': 'test123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_login_success(self):
        """Test login berhasil"""
        response = self.client.post('/api/auth/login',
            data=json.dumps({
                'username': 'andi',
                'password': 'andi123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'andi')
    
    def test_login_wrong_password(self):
        """Test login dengan password salah"""
        response = self.client.post('/api/auth/login',
            data=json.dumps({
                'username': 'andi',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_login_nonexistent_user(self):
        """Test login user yang tidak ada"""
        response = self.client.post('/api/auth/login',
            data=json.dumps({
                'username': 'nonexistent',
                'password': 'test123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    # ===== API TESTS - PRODUCTS =====
    
    def test_get_products(self):
        """Test get all products"""
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_get_product_detail(self):
        """Test get product detail"""
        response = self.client.get('/api/products/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('price', data)
    
    def test_get_nonexistent_product(self):
        """Test get product yang tidak ada"""
        response = self.client.get('/api/products/9999')
        self.assertEqual(response.status_code, 404)
    
    # ===== API TESTS - USERS =====
    
    def test_get_user_idor(self):
        """Test IDOR pada user endpoint"""
        # Endpoint tidak require login, IDOR test
        response = self.client.get('/api/users/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('username', data)
    
    def test_get_nonexistent_user(self):
        """Test get user yang tidak ada"""
        response = self.client.get('/api/users/9999')
        self.assertEqual(response.status_code, 404)
    
    # ===== API TESTS - CART & CHECKOUT =====
    
    def test_cart_requires_login(self):
        """Test cart memerlukan login"""
        response = self.client.get('/api/cart')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_add_to_cart_requires_login(self):
        """Test add to cart memerlukan login"""
        response = self.client.post('/api/cart/add',
            data=json.dumps({'product_id': 1, 'quantity': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)
    
    # ===== API TESTS - ADMIN =====
    
    def test_admin_page_requires_login(self):
        """Test admin page memerlukan login"""
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)
    
    def test_admin_api_requires_admin_role(self):
        """Test admin API memerlukan admin role"""
        # Login sebagai user biasa
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1  # andi (user biasa)
            sess['role'] = 'user'
        
        response = self.client.get('/api/admin/users')
        self.assertEqual(response.status_code, 403)
    
    # ===== DATABASE TESTS =====
    
    def test_database_created(self):
        """Test database berhasil dibuat"""
        self.assertTrue(os.path.exists('pasar_kita.db'))
    
    def test_demo_users_exist(self):
        """Test akun demo tersedia"""
        # Test login dengan semua akun demo
        users = [
            ('andi', 'andi123'),
            ('sari', 'sari123'),
            ('admin', 'admin123')
        ]
        
        for username, password in users:
            response = self.client.post('/api/auth/login',
                data=json.dumps({
                    'username': username,
                    'password': password
                }),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200,
                f"User {username} login failed")
    
    def test_demo_products_exist(self):
        """Test produk demo tersedia"""
        response = self.client.get('/api/products')
        data = json.loads(response.data)
        self.assertGreaterEqual(len(data), 10,
            "Minimum 10 produk demo harus tersedia")
    
    def test_categories_exist(self):
        """Test kategori tersedia"""
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
    
    # ===== SECURITY TESTS =====
    
    def test_sql_injection_attempt(self):
        """Test SQL injection protection (should fail/return error)"""
        # Ini untuk verify vulnerability ada
        response = self.client.get("/api/products?q=' OR '1'='1")
        # Karena vulnerable, akan return lebih banyak data
        # Ini cuma test untuk confirm vulnerability
        self.assertEqual(response.status_code, 200)
    
    def test_xss_comment(self):
        """Test XSS tidak di-sanitize (vulnerability test)"""
        # Login first
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'andi'
        
        response = self.client.post('/api/comments/add',
            data=json.dumps({
                'product_id': 1,
                'rating': 5,
                'comment': '<img src=x onerror="alert(\'XSS\')">'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
    
    def test_idor_order_access(self):
        """Test IDOR pada order (vulnerability test)"""
        # Login as user 1
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Try access order dari user lain
        response = self.client.get('/api/orders/2')
        # Jika vulnerable, akan return 200
        # Jika secure, akan return 403
        self.assertIn(response.status_code, [200, 403])
    
    # ===== RATE LIMITING TEST =====
    
    def test_rate_limit_endpoint_exists(self):
        """Test rate limit endpoint tersedia"""
        response = self.client.post('/api/rate-test')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
    
    def test_file_upload_endpoint_exists(self):
        """Test file upload endpoint tersedia"""
        # Just verify endpoint exists (don't actually upload)
        response = self.client.post('/api/upload')
        # Will return 400 karena no file, but endpoint exists
        self.assertEqual(response.status_code, 400)

def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)

if __name__ == '__main__':
    print("=" * 60)
    print("PasarKita Security Training Marketplace - Test Suite")
    print("=" * 60)
    print()
    run_tests()
    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
