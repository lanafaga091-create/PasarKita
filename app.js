// ===== GLOBAL STATE =====

let currentUser = null;
let cartItems = [];
let currentPage = 'home';

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    loadCurrentUser();
    initializeEventListeners();
});

// ===== USER FUNCTIONS =====

function loadCurrentUser() {
    const userId = localStorage.getItem('user_id');
    const username = localStorage.getItem('username');
    const role = localStorage.getItem('role');
    
    if (userId) {
        currentUser = {
            id: parseInt(userId),
            username: username,
            role: role
        };
        updateNavigation();
    }
}

function updateNavigation() {
    const authSection = document.getElementById('auth-section');
    if (!authSection) return;
    
    if (currentUser) {
        authSection.innerHTML = `
            <span>${currentUser.username}</span>
            <a href="/profile" class="btn btn-sm btn-outline">Profil</a>
            <button onclick="logout()" class="btn btn-sm btn-danger">Logout</button>
        `;
        
        if (currentUser.role === 'admin') {
            const adminLink = document.createElement('a');
            adminLink.href = '/admin';
            adminLink.className = 'btn btn-sm btn-secondary';
            adminLink.textContent = 'Admin Panel';
            authSection.appendChild(adminLink);
        }
    } else {
        authSection.innerHTML = `
            <a href="/login" class="btn btn-sm btn-outline">Login</a>
            <a href="/register" class="btn btn-sm btn-primary">Register</a>
        `;
    }
}

function registerUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const password_confirm = document.getElementById('password_confirm').value;
    
    if (password !== password_confirm) {
        showAlert('Password tidak cocok', 'danger');
        return;
    }
    
    fetch('/api/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            email: email,
            password: password
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Registrasi berhasil! Silakan login', 'success');
            setTimeout(() => window.location.href = '/login', 1500);
        }
    })
    .catch(err => showAlert('Terjadi kesalahan', 'danger'));
}

function loginUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            localStorage.setItem('user_id', data.user.id);
            localStorage.setItem('username', data.user.username);
            localStorage.setItem('role', data.user.role);
            showAlert('Login berhasil!', 'success');
            setTimeout(() => window.location.href = '/', 1000);
        }
    })
    .catch(err => showAlert('Terjadi kesalahan', 'danger'));
}

function logout() {
    fetch('/api/auth/logout', {
        method: 'POST'
    })
    .then(r => r.json())
    .then(data => {
        localStorage.clear();
        currentUser = null;
        window.location.href = '/';
    });
}

// ===== PRODUCT FUNCTIONS =====

function loadProducts(search = '', category = '') {
    let url = '/api/products';
    const params = new URLSearchParams();
    
    if (search) params.append('q', search);
    if (category) params.append('category', category);
    
    if (params.toString()) url += '?' + params.toString();
    
    fetch(url)
    .then(r => r.json())
    .then(products => {
        displayProducts(products);
    })
    .catch(err => console.error('Error loading products:', err));
}

function displayProducts(products) {
    const container = document.getElementById('products-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (products.length === 0) {
        container.innerHTML = '<p class="text-center">Tidak ada produk ditemukan</p>';
        return;
    }
    
    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-image">
                <img src="${product.image}" alt="${product.name}" onerror="this.src='/product.svg'">
            </div>
            <div class="card-body">
                <div class="card-title">${product.name}</div>
                <div class="card-text">${product.description.substring(0, 60)}...</div>
                <div class="flex-between">
                    <div class="price">Rp ${formatPrice(product.price)}</div>
                    <div class="badge ${product.stock > 0 ? 'badge-success' : 'badge-danger'}">
                        ${product.stock} stok
                    </div>
                </div>
            </div>
            <div class="card-footer">
                <a href="/product/${product.id}" class="btn btn-sm btn-primary">Lihat Detail</a>
            </div>
        `;
        
        container.appendChild(card);
    });
}

function formatPrice(price) {
    return new Intl.NumberFormat('id-ID').format(price);
}

// ===== CART FUNCTIONS =====

function addToCart(productId) {
    if (!currentUser) {
        showAlert('Silakan login terlebih dahulu', 'warning');
        window.location.href = '/login';
        return;
    }
    
    const quantity = document.getElementById('quantity')?.value || 1;
    
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: parseInt(quantity)
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Produk ditambahkan ke keranjang', 'success');
            loadCart();
        }
    })
    .catch(err => showAlert('Terjadi kesalahan', 'danger'));
}

function loadCart() {
    if (!currentUser) return;
    
    fetch('/api/cart')
    .then(r => r.json())
    .then(items => {
        cartItems = items;
        displayCart();
        updateCartBadge();
    })
    .catch(err => console.error('Error loading cart:', err));
}

function displayCart() {
    const container = document.getElementById('cart-items');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (cartItems.length === 0) {
        container.innerHTML = '<p class="text-center">Keranjang kosong</p>';
        updateCheckoutForm();
        return;
    }
    
    let total = 0;
    
    cartItems.forEach(item => {
        const subtotal = item.price * item.quantity;
        total += subtotal;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.name}</td>
            <td>Rp ${formatPrice(item.price)}</td>
            <td>
                <input type="number" value="${item.quantity}" min="1" max="${item.stock}"
                       onchange="updateCartItemQuantity(${item.id}, this.value)">
            </td>
            <td>Rp ${formatPrice(subtotal)}</td>
            <td>
                <button onclick="removeFromCart(${item.id})" class="btn btn-sm btn-danger">
                    Hapus
                </button>
            </td>
        `;
        container.appendChild(row);
    });
    
    updateCheckoutForm();
}

function removeFromCart(cartId) {
    fetch('/api/cart/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            cart_id: cartId
        })
    })
    .then(r => r.json())
    .then(data => {
        loadCart();
    });
}

function updateCartItemQuantity(cartId, quantity) {
    // Bisa di-extend untuk update quantity
}

function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        badge.textContent = cartItems.length;
    }
}

// ===== CHECKOUT FUNCTIONS =====

function updateCheckoutForm() {
    const subtotalEl = document.getElementById('subtotal');
    const discountEl = document.getElementById('discount');
    const totalEl = document.getElementById('total');
    
    if (!subtotalEl) return;
    
    let subtotal = 0;
    cartItems.forEach(item => {
        subtotal += item.price * item.quantity;
    });
    
    let discount = 0;
    const couponCode = document.getElementById('coupon_code')?.value || '';
    
    // Discount calculation
    if (couponCode) {
        // Get discount from server atau hitung di sini
        const discountPercent = getCouponDiscount(couponCode);
        if (discountPercent) {
            discount = subtotal * (discountPercent / 100);
        }
    }
    
    const total = subtotal - discount;
    
    subtotalEl.textContent = `Rp ${formatPrice(subtotal)}`;
    if (discountEl) discountEl.textContent = `-Rp ${formatPrice(discount)}`;
    if (totalEl) totalEl.textContent = `Rp ${formatPrice(Math.max(total, 0))}`;
}

function getCouponDiscount(code) {
    // Simple mapping - bisa request ke API
    const coupons = {
        'WELCOME10': 10,
        'WELCOME25': 25,
        'WELCOME50': 50
    };
    return coupons[code.toUpperCase()] || 0;
}

function applyCoupon() {
    updateCheckoutForm();
}

function checkout() {
    if (!currentUser) {
        showAlert('Silakan login terlebih dahulu', 'warning');
        return;
    }
    
    if (cartItems.length === 0) {
        showAlert('Keranjang kosong', 'danger');
        return;
    }
    
    const couponCode = document.getElementById('coupon_code')?.value || '';
    
    fetch('/api/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            coupon_code: couponCode
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Pesanan berhasil dibuat!', 'success');
            localStorage.setItem('last_order_id', data.order_id);
            setTimeout(() => window.location.href = '/orders', 1500);
        }
    })
    .catch(err => showAlert('Terjadi kesalahan', 'danger'));
}

// ===== ORDER FUNCTIONS =====

function loadOrders() {
    if (!currentUser) return;
    
    fetch('/api/orders')
    .then(r => r.json())
    .then(orders => {
        displayOrders(orders);
    })
    .catch(err => console.error('Error loading orders:', err));
}

function displayOrders(orders) {
    const container = document.getElementById('orders-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (orders.length === 0) {
        container.innerHTML = '<p class="text-center">Tidak ada pesanan</p>';
        return;
    }
    
    orders.forEach(order => {
        const statusBadge = getStatusBadge(order.status);
        
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-body">
                <div class="flex-between">
                    <div>
                        <div class="card-title">Pesanan #${order.id}</div>
                        <div class="card-text">${new Date(order.created_at).toLocaleDateString('id-ID')}</div>
                    </div>
                    <div>${statusBadge}</div>
                </div>
                <div class="mt-3 flex-between">
                    <div>
                        <div>Total: <strong>Rp ${formatPrice(order.total_price)}</strong></div>
                        ${order.discount > 0 ? `<div class="card-text">Diskon: Rp ${formatPrice(order.discount)}</div>` : ''}
                    </div>
                    <a href="/orders?id=${order.id}" class="btn btn-sm btn-primary">Lihat Detail</a>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

function getStatusBadge(status) {
    const statusMap = {
        'Pending': 'badge-warning',
        'Paid': 'badge-info',
        'Processing': 'badge-info',
        'Shipped': 'badge-primary',
        'Completed': 'badge-success',
        'Cancelled': 'badge-danger'
    };
    
    const badgeClass = statusMap[status] || 'badge-primary';
    return `<span class="badge ${badgeClass}">${status}</span>`;
}

// ===== PROFILE FUNCTIONS =====

function loadProfile() {
    if (!currentUser) return;
    
    fetch('/api/profile')
    .then(r => r.json())
    .then(user => {
        displayProfile(user);
    })
    .catch(err => console.error('Error loading profile:', err));
}

function displayProfile(user) {
    const container = document.getElementById('profile-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h3>Informasi Profil</h3>
                <div class="form-group mt-3">
                    <label>Username</label>
                    <input type="text" value="${user.username}" disabled>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="profile_email" value="${user.email}">
                </div>
                <div class="form-group">
                    <label>Nama Lengkap</label>
                    <input type="text" id="profile_name" value="${user.full_name || ''}">
                </div>
                <div class="form-group">
                    <label>Telepon</label>
                    <input type="tel" id="profile_phone" value="${user.phone || ''}">
                </div>
                <div class="form-group">
                    <label>Alamat</label>
                    <textarea id="profile_address">${user.address || ''}</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Kota</label>
                        <input type="text" id="profile_city" value="${user.city || ''}">
                    </div>
                    <div class="form-group">
                        <label>Kode Pos</label>
                        <input type="text" id="profile_postal" value="${user.postal_code || ''}">
                    </div>
                </div>
                <button onclick="updateProfile()" class="btn btn-primary">Simpan Perubahan</button>
            </div>
        </div>
    `;
}

function updateProfile() {
    const data = {
        email: document.getElementById('profile_email')?.value || '',
        full_name: document.getElementById('profile_name')?.value || '',
        phone: document.getElementById('profile_phone')?.value || '',
        address: document.getElementById('profile_address')?.value || '',
        city: document.getElementById('profile_city')?.value || '',
        postal_code: document.getElementById('profile_postal')?.value || ''
    };
    
    // VULNERABLE: Jika kirim 'role', bisa di-update
    // data.role = 'admin'; // Contoh attack
    
    fetch('/api/profile/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Profil berhasil diperbarui', 'success');
            loadProfile();
        }
    });
}

// ===== COMMENT FUNCTIONS =====

function loadProductComments(productId) {
    fetch(`/api/products/${productId}`)
    .then(r => r.json())
    .then(product => {
        displayComments(product.comments);
    });
}

function displayComments(comments) {
    const container = document.getElementById('comments-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    comments.forEach(comment => {
        const div = document.createElement('div');
        div.className = 'card mt-2';
        div.innerHTML = `
            <div class="card-body">
                <div class="flex-between mb-2">
                    <strong>${comment.username}</strong>
                    <span class="badge badge-primary">${comment.rating} ⭐</span>
                </div>
                <p class="card-text">${comment.comment}</p>
                <small class="text-muted">${new Date(comment.created_at).toLocaleDateString('id-ID')}</small>
            </div>
        `;
        
        container.appendChild(div);
    });
}

function addComment(productId) {
    if (!currentUser) {
        showAlert('Silakan login terlebih dahulu', 'warning');
        return;
    }
    
    const rating = document.getElementById('comment_rating').value;
    const comment = document.getElementById('comment_text').value;
    
    if (!comment.trim()) {
        showAlert('Komentar tidak boleh kosong', 'danger');
        return;
    }
    
    fetch('/api/comments/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            product_id: productId,
            rating: parseInt(rating),
            comment: comment
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Komentar ditambahkan', 'success');
            document.getElementById('comment_text').value = '';
            loadProductComments(productId);
        }
    });
}

// ===== SEARCH FUNCTIONS =====

function searchProducts(event) {
    event.preventDefault();
    
    const query = document.getElementById('search-input').value;
    loadProducts(query);
}

function filterByCategory(categoryId) {
    loadProducts('', categoryId);
}

// ===== UPLOAD FUNCTIONS =====

function uploadAvatar() {
    const fileInput = document.getElementById('avatar_file');
    if (!fileInput.files.length) {
        showAlert('Pilih file terlebih dahulu', 'danger');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Avatar berhasil diupload', 'success');
        }
    });
}

// ===== HELPER FUNCTIONS =====

function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'alert-container';
        document.body.insertBefore(container, document.body.firstChild);
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <strong>${type.toUpperCase()}</strong>: ${message}
        <button onclick="this.parentElement.remove()" style="float:right; background:none; border:none; cursor:pointer;">✕</button>
    `;
    
    container.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}

function initializeEventListeners() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', searchProducts);
    }
    
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', registerUser);
    }
    
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', loginUser);
    }
}

// ===== PAGE SPECIFIC INITIALIZATION =====

function initProductPage(productId) {
    fetch(`/api/products/${productId}`)
    .then(r => r.json())
    .then(product => {
        const container = document.getElementById('product-detail');
        if (container) {
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <img src="${product.image}" alt="${product.name}" 
                             style="width: 100%; border-radius: 12px;"
                             onerror="this.src='/product.svg'">
                    </div>
                    <div>
                        <h1>${product.name}</h1>
                        <p>${product.description}</p>
                        <div style="margin: 2rem 0;">
                            <div class="price" style="margin-bottom: 1rem;">Rp ${formatPrice(product.price)}</div>
                            <div class="badge ${product.stock > 0 ? 'badge-success' : 'badge-danger'}">
                                ${product.stock > 0 ? `${product.stock} tersedia` : 'Habis'}
                            </div>
                        </div>
                        <div class="form-group mt-3">
                            <label>Jumlah</label>
                            <input type="number" id="quantity" value="1" min="1" max="${product.stock}">
                        </div>
                        <button onclick="addToCart(${product.id})" 
                                class="btn btn-primary btn-lg"
                                ${product.stock <= 0 ? 'disabled' : ''}>
                            Tambah ke Keranjang
                        </button>
                    </div>
                </div>
            `;
        }
        
        displayComments(product.comments);
    });
}

// ===== RATE TEST =====

function testRateLimit() {
    let count = 0;
    const results = [];
    
    const interval = setInterval(() => {
        fetch('/api/rate-test', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            count++;
            results.push({
                attempt: count,
                status: r.status,
                time: new Date().toISOString()
            });
            
            if (count >= 50) {
                clearInterval(interval);
                console.log('Rate limit test results:', results);
                showAlert(`Test selesai: ${count} requests`, 'info');
            }
        });
    }, 100);
}
