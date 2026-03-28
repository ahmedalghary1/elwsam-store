// Cart Manager (Hybrid System) - Improved Version
(function() {
    if (window.CartManager || window.cartManager) {
        console.warn('CartManager already defined. Skipping redefinition.');
        return;
    }

    class CartManager {
        constructor() {
            this.cartKey = 'noor_cart';
            this.init();
        }
        
        init() {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.runInit());
            } else {
                this.runInit();
            }
        }

        runInit() {
            this.cleanupCart();
            this.updateCartBadge();
            this.bindAddToCartButtons();
            this.initCartPage();
            this.syncCartOnLogin();
        }

        cleanupCart() {
            const cart = this.getCart();
            const cleaned = cart.filter(item =>
                item.product_id !== undefined &&
                item.product_id !== null &&
                String(item.product_id) !== 'undefined'
            );
            if (cleaned.length !== cart.length) {
                this.saveCart(cleaned);
            }
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
        // Guest Add (returns Promise)
        // ==============================
        addToCart(productId, variantId = null, quantity = 1, productData = {}) {
            return new Promise((resolve) => {
                const cart = this.getCart();
                const existingItem = cart.find(item => item.product_id == productId && item.variant_id == variantId);
                if (existingItem) {
                    existingItem.quantity += quantity;
                } else {
                    const newItem = {
                        product_id: productId,
                        variant_id: variantId,
                        quantity: quantity,
                        name: productData.name || 'منتج',
                        price: parseFloat(productData.price) || 0,
                        image: productData.image || ''   // قد تكون فارغة
                    };
                    cart.push(newItem);
                }
                this.saveCart(cart);
                this.showToast('تم إضافة المنتج للسلة');
                if (document.querySelector('.cart-page')) this.renderGuestCart();
                resolve(true);
            });
        }

        // ==============================
        // Authenticated Add (returns Promise)
        // ==============================
        addToCartAjax(productId, variantId = null, quantity = 1) {
            const formData = new URLSearchParams();
            formData.append('product_id', productId);
            if (variantId) formData.append('variant_id', variantId);
            formData.append('quantity', quantity);

            return fetch('/orders/cart/add/', {
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
                    if (document.querySelector('.cart-page')) location.reload();
                    return true;
                } else if (data.login_required) {
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                    return false;
                } else {
                    this.showToast(data.message || 'حدث خطأ');
                    return false;
                }
            })
            .catch(err => {
                console.error('AJAX error:', err);
                // Return special error object to trigger fallback
                return { error: true, message: err };
            });
        }

        // دالة مساعدة لمقارنة المتغيرات
        _findCartItem(cart, productId, variantId) {
            const normalizedVariant = (variantId === '' || variantId === undefined || variantId === null) ? null : variantId;
            return cart.find(item => {
                // تحويل product_id إلى سلسلة للمقارنة الآمنة
                const itemProductId = String(item.product_id);
                const searchProductId = String(productId);
                const matchProduct = itemProductId === searchProductId;
                const matchVariant = item.variant_id === normalizedVariant;
                return matchProduct && matchVariant;
            });
        }

        updateGuestQuantity(productId, variantId, quantity) {
            console.log('updateGuestQuantity called', productId, variantId, quantity);
            const cart = this.getCart();
            const item = this._findCartItem(cart, productId, variantId);
            if (item) {
                item.quantity = Math.max(1, quantity);
                this.saveCart(cart);
                this.renderGuestCart();
            } else {
                console.warn('Item not found for update', productId, variantId);
            }
        }

        removeFromGuestCart(productId, variantId) {
            console.log('removeFromGuestCart called', productId, variantId);
            const cart = this.getCart();
            const newCart = cart.filter(item => {
                const matchProduct = String(item.product_id) === String(productId);
                const normalizedVariant = (variantId === '' || variantId === undefined || variantId === null) ? null : variantId;
                const matchVariant = item.variant_id === normalizedVariant;
                // نريد الاحتفاظ بالعناصر التي لا تطابق
                return !(matchProduct && matchVariant);
            });
            this.saveCart(newCart);
            this.showToast('تم حذف المنتج');
            this.renderGuestCart();
        }

        // ==============================
        // Authenticated Update via AJAX
        // ==============================
        updateCartItemAjax(itemId, quantity) {
            const formData = new URLSearchParams();
            formData.append('quantity', quantity);

            return fetch(`/orders/cart/item/${itemId}/update-ajax/`, {
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
                        // Update item total
                        const totalSpan = document.querySelector(`.cart-item[data-item-id="${itemId}"] .total-price`);
                        if (totalSpan && data.item_total !== undefined) {
                            totalSpan.textContent = parseFloat(data.item_total).toFixed(2) + ' جنيه';
                        }
                        
                        // Update cart totals
                        const subtotalSpan = document.getElementById('subtotal');
                        const totalSpanCart = document.getElementById('total');
                        if (data.cart_total !== undefined) {
                            const cartTotal = parseFloat(data.cart_total).toFixed(2);
                            if (subtotalSpan) subtotalSpan.textContent = cartTotal + ' جنيه';
                            if (totalSpanCart) totalSpanCart.textContent = cartTotal + ' جنيه';
                        }
                        
                        // Update badge
                        this.updateCartBadge();
                    }
                } else {
                    this.showToast(data.error || 'حدث خطأ');
                    location.reload(); // Reload to sync state
                }
            })
            .catch(err => {
                console.error('Update cart error:', err);
                this.showToast('خطأ في الاتصال بالسيرفر');
                location.reload();
            });
        }

        removeCartItemAjax(itemId) {
            return fetch(`/orders/cart/item/${itemId}/remove-ajax/`, {
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
                    location.reload();
                }
            })
            .catch(err => {
                console.error('Remove cart error:', err);
                this.showToast('خطأ في الاتصال بالسيرفر');
                location.reload();
            });
        }

        // ==============================
        // Badge
        // ==============================
        updateCartBadge() {
            if (this.isAuthenticated()) {
                // For authenticated users, count from DOM if on cart page
                const cartItems = document.querySelectorAll('.cart-item[data-item-id]');
                if (cartItems.length > 0) {
                    let count = 0;
                    cartItems.forEach(item => {
                        const qtyInput = item.querySelector('.quantity-input');
                        count += parseInt(qtyInput?.value || 0);
                    });
                    this.updateCartBadgeFromServer(count);
                } else {
                    // Keep existing badge value if not on cart page
                    const existingBadge = document.querySelector('.cart-count');
                    const existingCount = existingBadge ? parseInt(existingBadge.textContent) || 0 : 0;
                    this.updateCartBadgeFromServer(existingCount);
                }
            } else {
                // For guests, use localStorage
                const count = this.getCartCount();
                document.querySelectorAll('.cart-count').forEach(el => {
                    el.textContent = count;
                    el.style.display = count > 0 ? 'flex' : 'none';
                });
            }
        }

        updateCartBadgeFromServer(count) {
            document.querySelectorAll('.cart-count').forEach(el => {
                el.textContent = count;
                el.style.display = count > 0 ? 'flex' : 'none';
            });
        }

        getCartCount() {
            return this.getCart().reduce((c, item) => c + (item.quantity || 0), 0);
        }

        // ==============================
        // Add To Cart Buttons
        // ==============================
        bindAddToCartButtons() {
            if (this._addToCartBound) return;
            this._addToCartBound = true;

            document.addEventListener('click', (e) => {
                const btn = e.target.closest('[data-action="add-to-cart"]');
                if (!btn) return;

                e.preventDefault();
                e.stopPropagation();

                if (btn.disabled) return;
                btn.disabled = true;

                const productId = btn.dataset.productId;
                if (!productId) {
                    btn.disabled = false;
                    return;
                }

                let quantity = 1;
                const qtyInput = document.querySelector(`.qty-input[data-product-id="${productId}"]`);
                if (qtyInput) {
                    let qtyVal = parseInt(qtyInput.value, 10);
                    if (!isNaN(qtyVal) && qtyVal >= 1 && qtyVal <= 99) {
                        quantity = qtyVal;
                    }
                } else {
                    const qtyDisplay = document.getElementById('qty-display');
                    if (qtyDisplay) {
                        let qtyVal = parseInt(qtyDisplay.textContent, 10);
                        if (!isNaN(qtyVal) && qtyVal >= 1 && qtyVal <= 99) {
                            quantity = qtyVal;
                        }
                    } else {
                        quantity = parseInt(btn.dataset.quantity || '1', 10);
                    }
                }

                const productData = {
                    name: btn.dataset.productName || 'منتج',
                    price: parseFloat(btn.dataset.productPrice) || 0,
                    image: btn.dataset.productImage || ''
                };

                let promise;
                if (this.isAuthenticated()) {
                    // محاولة AJAX أولاً، مع fallback إلى localStorage عند الفشل
                    promise = this.addToCartAjax(productId, null, quantity).then(result => {
                        // إذا كان هناك خطأ أو فشل، استخدم localStorage
                        if (!result || result === false || (result && result.error)) {
                            console.log('AJAX failed, using localStorage fallback');
                            return this.addToCart(productId, null, quantity, productData);
                        }
                        return result;
                    });
                } else {
                    promise = this.addToCart(productId, null, quantity, productData);
                }

                promise.then(() => {
                    btn.disabled = false;
                }).catch(err => {
                    console.error('Add to cart error:', err);
                    // fallback to localStorage on error
                    this.addToCart(productId, null, quantity, productData);
                    btn.disabled = false;
                });
            });
        }

        // ==============================
        // Cart Page Initialization
        // ==============================
        initCartPage() {
            if (!document.querySelector('.cart-page')) return;

            if (this.isAuthenticated()) {
                this.bindAuthenticatedCartEvents();
            } else {
                this.renderGuestCart();
                this.setupGuestCartDelegation();
            }
        }

        setupGuestCartDelegation() {
            const container = document.getElementById('guest-cart-items');
            if (!container) return;
            // إزالة المستمع السابق إذا وجد
            if (this._guestDelegationHandler) {
                container.removeEventListener('click', this._guestDelegationHandler);
            }
            this._guestDelegationHandler = (e) => {
                const btn = e.target.closest('.quantity-btn');
                if (btn) {
                    e.preventDefault();
                    const itemDiv = btn.closest('.cart-item');
                    if (!itemDiv) return;
                    const productId = itemDiv.getAttribute('data-product-id');
                    const variantId = itemDiv.getAttribute('data-variant-id') || '';
                    const input = itemDiv.querySelector('.quantity-input');
                    let qty = parseInt(input.value, 10);
                    if (btn.classList.contains('minus')) {
                        qty = Math.max(1, qty - 1);
                    } else if (btn.classList.contains('plus')) {
                        qty = qty + 1;
                    }
                    input.value = qty;
                    this.updateGuestQuantity(productId, variantId, qty);
                }
                const removeBtn = e.target.closest('.remove-btn');
                if (removeBtn) {
                    e.preventDefault();
                    const itemDiv = removeBtn.closest('.cart-item');
                    if (!itemDiv) return;
                    const productId = itemDiv.getAttribute('data-product-id');
                    const variantId = itemDiv.getAttribute('data-variant-id') || '';
                    this.removeFromGuestCart(productId, variantId);
                }
            };
            container.addEventListener('click', this._guestDelegationHandler);
        }

        bindAuthenticatedCartEvents() {
            const cartItems = document.querySelector('.cart-items');
            if (!cartItems) return;

            // Event delegation for authenticated cart
            cartItems.addEventListener('click', (e) => {
                // Handle quantity buttons
                const qtyBtn = e.target.closest('.quantity-btn');
                if (qtyBtn) {
                    e.preventDefault();
                    const cartItem = qtyBtn.closest('.cart-item');
                    if (!cartItem) return;

                    const itemId = cartItem.dataset.itemId;
                    const qtyInput = cartItem.querySelector('.quantity-input');
                    let currentQty = parseInt(qtyInput.value) || 1;

                    if (qtyBtn.dataset.action === 'increase' || qtyBtn.classList.contains('plus')) {
                        currentQty++;
                    } else if (qtyBtn.dataset.action === 'decrease' || qtyBtn.classList.contains('minus')) {
                        currentQty = Math.max(1, currentQty - 1);
                    }

                    qtyInput.value = currentQty;
                    this.updateCartItemAjax(itemId, currentQty);
                }

                // Handle remove button
                const removeBtn = e.target.closest('.remove-btn');
                if (removeBtn) {
                    e.preventDefault();
                    const itemId = removeBtn.dataset.itemId;
                    if (itemId && confirm('هل تريد حذف هذا المنتج من السلة؟')) {
                        this.removeCartItemAjax(itemId);
                    }
                }
            });

            // Handle direct input changes
            cartItems.addEventListener('change', (e) => {
                if (e.target.classList.contains('quantity-input')) {
                    const cartItem = e.target.closest('.cart-item');
                    if (!cartItem) return;

                    const itemId = cartItem.dataset.itemId;
                    let qty = parseInt(e.target.value) || 1;
                    qty = Math.max(1, Math.min(99, qty));
                    e.target.value = qty;
                    this.updateCartItemAjax(itemId, qty);
                }
            });
        }

        renderGuestCart() {
            const cart = this.getCart();
            const container = document.getElementById('guest-cart-items');
            const summaryDiv = document.getElementById('cart-content-guest');
            const emptyDiv = document.getElementById('guest-empty-cart');

            if (!container) return;

            if (cart.length === 0) {
                if (summaryDiv) summaryDiv.style.display = 'none';
                if (emptyDiv) emptyDiv.style.display = 'block';
                container.innerHTML = '';
                return;
            }

            if (summaryDiv) summaryDiv.style.display = 'block';
            if (emptyDiv) emptyDiv.style.display = 'none';

            // SVG افتراضي (مستطيل مع أيقونة صورة)
            const defaultSvg = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="%23999" stroke-width="1.5"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"%3E%3C/rect%3E%3Ccircle cx="8.5" cy="8.5" r="1.5"%3E%3C/circle%3E%3Cpolyline points="21 15 16 10 5 21"%3E%3C/polyline%3E%3C/svg%3E';

            container.innerHTML = cart.map(item => {
                const qty = item.quantity && !isNaN(item.quantity) ? item.quantity : 1;
                const price = item.price && !isNaN(item.price) ? item.price : 0;
                const name = escapeHtml(item.name) || 'منتج';
                // استخدام الصورة المخزنة أو الافتراضية
                const imgSrc = item.image && item.image.trim() !== '' ? item.image : defaultSvg;
                const variantIdAttr = (item.variant_id !== null && item.variant_id !== undefined) ? item.variant_id : '';
                return `
                    <div class="cart-item" data-product-id="${item.product_id}" data-variant-id="${variantIdAttr}">
                        <div class="item-image">
                            <img src="${imgSrc}" alt="${name}" onerror="this.onerror=null;this.src='${defaultSvg}';">
                        </div>
                        <div class="item-details">
                            <h3>${name}</h3>
                            <p class="item-price">${price.toFixed(2)} جنيه</p>
                        </div>
                        <div class="item-quantity">
                            <button class="quantity-btn minus">-</button>
                            <input type="number" class="quantity-input" value="${qty}" min="1" max="99">
                            <button class="quantity-btn plus">+</button>
                        </div>
                        <div class="item-total">
                            <p class="total-price">${(price * qty).toFixed(2)} جنيه</p>
                        </div>
                        <div class="item-actions">
                            <button class="remove-btn">✕</button>
                        </div>
                    </div>
                `;
            }).join('');

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
            return this.getCart().reduce((total, item) => {
                const price = parseFloat(item.price) || 0;
                const qty = parseInt(item.quantity) || 0;
                return total + (price * qty);
            }, 0);
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
                font-family: sans-serif;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        if (!window.cartManager) {
            window.cartManager = new CartManager();
        }
    });

    window.CartManager = CartManager;
})();
