// Cart Manager (Hybrid System)
class CartManager {
    constructor() {
        this.cartKey = 'noor_cart';
        this.init();
    }

    init() {
        this.updateCartBadge();
        this.bindAddToCartButtons();
        this.initCartPage();
        this.syncCartOnLogin();
    }

    isAuthenticated() {
        return document.body.dataset.auth === 'true';
    }

    // ==============================
    // LocalStorage (Guest)
    // ==============================
    getCart() {
        try {
            return JSON.parse(localStorage.getItem(this.cartKey) || '[]');
        } catch {
            return [];
        }
    }

    saveCart(cart) {
        localStorage.setItem(this.cartKey, JSON.stringify(cart));
        this.updateCartBadge();
    }

    clearCart() {
        this.saveCart([]);
    }

    // ==============================
    // Guest Add
    // ==============================
    addToCart(productId, variantId = null, quantity = 1, productData = {}) {
        const cart = this.getCart();
        const existingItem = cart.find(item => item.product_id == productId && item.variant_id == variantId);
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            cart.push({
                product_id: productId,
                variant_id: variantId,
                quantity: quantity,
                ...productData
            });
        }
        this.saveCart(cart);
        this.showToast('تم إضافة المنتج للسلة');
        if (document.querySelector('.cart-page')) this.renderGuestCart();
    }

    // ==============================
    // Authenticated Add (AJAX)
    // ==============================
    addToCartAjax(productId, variantId = null, quantity = 1) {
        const formData = new URLSearchParams();
        formData.append('product_id', productId);
        if (variantId) formData.append('variant_id', variantId);
        formData.append('quantity', quantity);

        fetch('/orders/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message);
                this.updateCartBadgeFromServer(data.cart_count);
                if (document.querySelector('.cart-page')) location.reload(); // تحديث صفحة السلة
            } else if (data.login_required) {
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
            } else {
                this.showToast(data.message || 'حدث خطأ');
            }
        })
        .catch(() => this.showToast('خطأ في الاتصال بالسيرفر'));
    }

    // ==============================
    // Guest Remove
    // ==============================
    removeFromGuestCart(productId, variantId = null) {
        const cart = this.getCart().filter(item => !(item.product_id == productId && item.variant_id == variantId));
        this.saveCart(cart);
        this.showToast('تم حذف المنتج');
        if (document.querySelector('.cart-page')) this.renderGuestCart();
    }

    // ==============================
    // Guest Update Quantity
    // ==============================
    updateGuestQuantity(productId, variantId, quantity) {
        const cart = this.getCart();
        const item = cart.find(item => item.product_id == productId && item.variant_id == variantId);
        if (item) {
            item.quantity = Math.max(1, quantity);
            this.saveCart(cart);
        }
        if (document.querySelector('.cart-page')) this.renderGuestCart();
    }

    // ==============================
    // Authenticated Update via AJAX
    // ==============================
    updateCartItemAjax(itemId, quantity) {
        const formData = new URLSearchParams();
        formData.append('quantity', quantity);

        fetch(`/orders/cart/update-ajax/${itemId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.showToast('تم تحديث الكمية');
                if (data.deleted) {
                    location.reload();
                } else {
                    document.querySelector(`.cart-item[data-item-id="${itemId}"] .cart-item-price`).textContent = data.item_total + ' ج.م';
                    document.getElementById('subtotal').textContent = data.cart_total + ' ج.م';
                    document.getElementById('total').textContent = data.cart_total + ' ج.م';
                }
            } else {
                this.showToast(data.error || 'حدث خطأ');
            }
        });
    }

    removeCartItemAjax(itemId) {
        fetch(`/orders/cart/remove-ajax/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.showToast('تم حذف المنتج');
                location.reload();
            } else {
                this.showToast(data.error || 'حدث خطأ');
            }
        });
    }

    // ==============================
    // Badge
    // ==============================
    updateCartBadge() {
        const count = this.getCartCount();
        document.querySelectorAll('.cart-count').forEach(el => {
            el.textContent = count;
            el.style.display = count > 0 ? 'flex' : 'none';
        });
    }

    updateCartBadgeFromServer(count) {
        document.querySelectorAll('.cart-count').forEach(el => {
            el.textContent = count;
            el.style.display = count > 0 ? 'flex' : 'none';
        });
    }

    getCartCount() {
        return this.getCart().reduce((c, item) => c + item.quantity, 0);
    }

    // ==============================
    // Add To Cart Buttons
    // ==============================
    bindAddToCartButtons() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action="add-to-cart"]');
            if (!btn) return;

            e.preventDefault();
            const productId = btn.dataset.productId;
            const quantity = parseInt(btn.dataset.quantity || 1);

            if (!productId) return;

            if (this.isAuthenticated()) {
                this.addToCartAjax(productId, null, quantity);
            } else {
                const productData = {
                    name: btn.dataset.productName || 'منتج',
                    price: parseFloat(btn.dataset.productPrice) || 0,
                    image: btn.dataset.productImage || ''
                };
                this.addToCart(productId, null, quantity, productData);
            }
        });
    }

    // ==============================
    // Cart Page Initialization
    // ==============================
    initCartPage() {
        if (!document.querySelector('.cart-page')) return;

        if (this.isAuthenticated()) {
            // للمستخدم المسجل: نربط أحداث تحديث وحذف المنتجات الموجودة
            this.bindAuthenticatedCartEvents();
        } else {
            // للضيف: نعرض السلة من localStorage ونديرها
            this.renderGuestCart();
            this.bindGuestCartEvents();
        }
    }

    bindAuthenticatedCartEvents() {
        // تحديث الكمية
        document.querySelectorAll('.cart-qty-btn, .cart-qty-val').forEach(el => {
            el.addEventListener('click', (e) => {
                const itemDiv = e.target.closest('.cart-item');
                if (!itemDiv) return;
                const itemId = itemDiv.dataset.itemId;
                const input = itemDiv.querySelector('.cart-qty-val');
                let quantity = parseInt(input.value);

                if (e.target.classList.contains('minus')) {
                    quantity = Math.max(1, quantity - 1);
                    input.value = quantity;
                } else if (e.target.classList.contains('plus')) {
                    quantity = quantity + 1;
                    input.value = quantity;
                } else {
                    quantity = parseInt(input.value);
                }
                this.updateCartItemAjax(itemId, quantity);
            });
        });

        // حذف العنصر
        document.querySelectorAll('.cart-remove-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = e.target.closest('.cart-item').dataset.itemId;
                if (confirm('هل تريد حذف هذا المنتج؟')) {
                    this.removeCartItemAjax(itemId);
                }
            });
        });
    }

    renderGuestCart() {
        const cart = this.getCart();
        const container = document.getElementById('guest-cart-items');
        const summaryDiv = document.getElementById('cart-content-guest');
        const emptyDiv = document.getElementById('guest-empty-cart');

        if (!container) return;

        if (cart.length === 0) {
            summaryDiv.style.display = 'none';
            emptyDiv.style.display = 'block';
            return;
        }

        summaryDiv.style.display = 'block';
        emptyDiv.style.display = 'none';

        container.innerHTML = cart.map(item => `
            <div class="cart-item" data-product-id="${item.product_id}" data-variant-id="${item.variant_id || ''}">
                <div class="cart-item-img">
                    <img src="${item.image || '/static/image/no-image.png'}">
                </div>
                <div class="cart-item-content">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-price">${item.price} ج.م</div>
                    <div class="cart-item-controls">
                        <div class="cart-qty">
                            <button class="cart-qty-btn minus">−</button>
                            <input type="number" class="cart-qty-val" value="${item.quantity}" min="1">
                            <button class="cart-qty-btn plus">+</button>
                        </div>
                        <button class="cart-remove-btn">✕</button>
                    </div>
                </div>
            </div>
        `).join('');

        this.updateGuestSummary();
    }

    updateGuestSummary() {
        const total = this.getCartTotal();
        const subtotalEl = document.getElementById('guest-subtotal');
        const totalEl = document.getElementById('guest-total');
        if (subtotalEl) subtotalEl.textContent = total.toFixed(2) + ' ج.م';
        if (totalEl) totalEl.textContent = total.toFixed(2) + ' ج.م';
    }

    getCartTotal() {
        return this.getCart().reduce((t, i) => t + (i.price * i.quantity), 0);
    }

    bindGuestCartEvents() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.cart-remove-btn');
            if (btn) {
                const item = btn.closest('.cart-item');
                const productId = item.dataset.productId;
                const variantId = item.dataset.variantId;
                this.removeFromGuestCart(productId, variantId);
            }

            const minusBtn = e.target.closest('.cart-qty-btn.minus');
            if (minusBtn) {
                const item = minusBtn.closest('.cart-item');
                const productId = item.dataset.productId;
                const variantId = item.dataset.variantId;
                const input = item.querySelector('.cart-qty-val');
                let qty = parseInt(input.value) - 1;
                if (qty < 1) qty = 1;
                input.value = qty;
                this.updateGuestQuantity(productId, variantId, qty);
            }

            const plusBtn = e.target.closest('.cart-qty-btn.plus');
            if (plusBtn) {
                const item = plusBtn.closest('.cart-item');
                const productId = item.dataset.productId;
                const variantId = item.dataset.variantId;
                const input = item.querySelector('.cart-qty-val');
                let qty = parseInt(input.value) + 1;
                input.value = qty;
                this.updateGuestQuantity(productId, variantId, qty);
            }
        });
    }

    // ==============================
    // Sync after login
    // ==============================
    syncCartOnLogin() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('login') === 'success' && this.getCart().length > 0) {
            this.syncCartWithServer();
        }
    }

    syncCartWithServer() {
        const cart = this.getCart();
        if (!cart.length) return;

        fetch('/orders/cart/sync/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `cart_data=${encodeURIComponent(JSON.stringify(cart))}`
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.clearCart();
                this.showToast('تم مزامنة السلة مع حسابك');
                setTimeout(() => location.reload(), 1000);
            }
        });
    }

    // ==============================
    // CSRF Token
    // ==============================
    getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.content;
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #22c55e;
            color: #fff;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 9999;
            font-size: 14px;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.cartManager = new CartManager();
});