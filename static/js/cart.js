// Cart functionality for guest users using localStorage
class CartManager {
    constructor() {
        this.cartKey = 'noor_cart';
        this.init();
    }

    init() {
        // Sync cart with server when user logs in
        this.syncCartOnLogin();

        // Update cart badge on page load
        this.updateCartBadge();

        // Handle add to cart buttons
        this.bindAddToCartButtons();

        // Handle cart page functionality
        this.initCartPage();
    }

    // Get cart from localStorage
    getCart() {
        try {
            return JSON.parse(localStorage.getItem(this.cartKey) || '[]');
        } catch (e) {
            return [];
        }
    }

    // Save cart to localStorage
    saveCart(cart) {
        localStorage.setItem(this.cartKey, JSON.stringify(cart));
        this.updateCartBadge();
    }

    // Add to cart via AJAX (for authenticated users)
    addToCartAjax(productId, variantId = null, quantity = 1) {
        const formData = new URLSearchParams();
        formData.append('product_id', productId);
        if (variantId) formData.append('variant_id', variantId);
        formData.append('quantity', quantity);

        fetch('/orders/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast('تم إضافة المنتج للسلة');
                // Optionally update cart count from server
                if (data.cart_count !== undefined) {
                    this.updateCartBadgeFromServer(data.cart_count);
                }
            } else {
                this.showToast(data.message || 'حدث خطأ أثناء إضافة المنتج للسلة');
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            this.showToast('حدث خطأ أثناء إضافة المنتج للسلة');
        });
    }
        const cart = this.getCart();
        const existingItem = cart.find(item =>
            item.product_id == productId &&
            item.variant_id == variantId
        );

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
    }

    // Remove item from cart
    removeFromCart(productId, variantId = null) {
        const cart = this.getCart().filter(item =>
            !(item.product_id == productId && item.variant_id == variantId)
        );
        this.saveCart(cart);
        this.showToast('تم حذف المنتج من السلة');
    }

    // Update item quantity
    updateQuantity(productId, variantId = null, quantity) {
        const cart = this.getCart();
        const item = cart.find(item =>
            item.product_id == productId &&
            item.variant_id == variantId
        );

        if (item) {
            item.quantity = Math.max(1, quantity);
            this.saveCart(cart);
        }
    }

    // Get cart total
    getCartTotal() {
        return this.getCart().reduce((total, item) => total + (item.price * item.quantity), 0);
    }

    // Get cart count
    getCartCount() {
        return this.getCart().reduce((count, item) => count + item.quantity, 0);
    }

    // Clear cart
    clearCart() {
        this.saveCart([]);
    }

    // Update cart badge from server data
    updateCartBadgeFromServer(count) {
        document.querySelectorAll('.cart-count').forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        });
    }

    // Bind add to cart buttons
    bindAddToCartButtons() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-action="add-to-cart"]');
            if (!button) return;

            e.preventDefault();

            const productId = button.dataset.productId;
            const quantity = parseInt(button.dataset.quantity) || 1;

            // Check if user is authenticated
            const isAuthenticated = document.querySelector('[data-authenticated="true"]') !== null;

            if (isAuthenticated) {
                // User is logged in, use AJAX
                this.addToCartAjax(productId, null, quantity);
            } else {
                // User is not logged in, use localStorage
                const productData = {
                    name: button.dataset.productName || 'منتج',
                    price: parseFloat(button.dataset.productPrice) || 0,
                    image: button.dataset.productImage || ''
                };
                this.addToCart(productId, null, quantity, productData);
            }
        });
    }

    // Initialize cart page functionality
    initCartPage() {
        if (!document.querySelector('.cart-page')) return;

        this.renderCartPage();
        this.bindCartPageEvents();
    }

    // Render cart items on cart page
    renderCartPage() {
        const cart = this.getCart();
        const cartContainer = document.querySelector('.cart-items');

        if (!cartContainer) return;

        if (cart.length === 0) {
            // Show empty cart
            document.querySelector('.cart-page').innerHTML = `
                <div class="container">
                    <div class="empty-cart">
                        <div class="empty-cart-icon">
                            <i class="fas fa-shopping-cart"></i>
                        </div>
                        <h2>سلة التسوق فارغة</h2>
                        <p>لم تقم بإضافة أي منتجات للسلة بعد</p>
                        <a href="{% url 'products:product_list' %}" class="btn btn-primary">تصفح المنتجات</a>
                    </div>
                </div>
            `;
            return;
        }

        // Render cart items (this would need to be implemented with actual product data from server)
        // For now, just show basic structure
        cartContainer.innerHTML = cart.map(item => `
            <div class="cart-item" data-product-id="${item.product_id}" data-variant-id="${item.variant_id}">
                <div class="item-image">
                    <img src="${item.image || '/static/image/no-image.png'}" alt="${item.name}">
                </div>
                <div class="item-details">
                    <h3>${item.name}</h3>
                    <p class="item-price">${item.price} ريال</p>
                </div>
                <div class="item-quantity">
                    <button class="quantity-btn minus" data-action="decrease">-</button>
                    <input type="number" class="quantity-input" value="${item.quantity}" min="1" max="99">
                    <button class="quantity-btn plus" data-action="increase">+</button>
                </div>
                <div class="item-total">
                    <p class="total-price">${(item.price * item.quantity).toFixed(2)} ريال</p>
                </div>
                <div class="item-actions">
                    <button class="remove-btn" data-product-id="${item.product_id}" data-variant-id="${item.variant_id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');

        this.updateCartSummary();
    }

    // Bind cart page events
    bindCartPageEvents() {
        // Quantity buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.quantity-btn');
            if (!btn) return;

            const item = btn.closest('.cart-item');
            const input = item.querySelector('.quantity-input');
            const action = btn.dataset.action;
            let quantity = parseInt(input.value);

            if (action === 'increase') {
                quantity++;
            } else if (action === 'decrease' && quantity > 1) {
                quantity--;
            }

            input.value = quantity;
            this.updateQuantity(
                item.dataset.productId,
                item.dataset.variantId,
                quantity
            );
            this.updateCartItemTotal(item);
            this.updateCartSummary();
        });

        // Quantity input change
        document.addEventListener('change', (e) => {
            if (!e.target.classList.contains('quantity-input')) return;

            const item = e.target.closest('.cart-item');
            const quantity = parseInt(e.target.value);

            if (quantity > 0) {
                this.updateQuantity(
                    item.dataset.productId,
                    item.dataset.variantId,
                    quantity
                );
                this.updateCartItemTotal(item);
                this.updateCartSummary();
            }
        });

        // Remove buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.remove-btn');
            if (!btn) return;

            if (confirm('هل أنت متأكد من حذف هذا المنتج من السلة؟')) {
                this.removeFromCart(
                    btn.dataset.productId,
                    btn.dataset.variantId
                );
                btn.closest('.cart-item').remove();
                this.updateCartSummary();
                this.checkEmptyCart();
            }
        });
    }

    // Update cart item total
    updateCartItemTotal(item) {
        const input = item.querySelector('.quantity-input');
        const price = parseFloat(item.querySelector('.item-price').textContent.replace(' ريال', ''));
        const quantity = parseInt(input.value);
        const totalElement = item.querySelector('.total-price');

        totalElement.textContent = (price * quantity).toFixed(2) + ' ريال';
    }

    // Update cart summary
    updateCartSummary() {
        const subtotalElement = document.getElementById('subtotal');
        const totalElement = document.getElementById('total');

        if (subtotalElement && totalElement) {
            const total = this.getCartTotal();
            subtotalElement.textContent = total.toFixed(2) + ' ريال';
            totalElement.textContent = total.toFixed(2) + ' ريال';
        }

        // Update cart count
        const countElement = document.getElementById('cart-count');
        if (countElement) {
            countElement.textContent = this.getCartCount() + ' منتج';
        }
    }

    // Check if cart is empty
    checkEmptyCart() {
        const items = document.querySelectorAll('.cart-item');
        if (items.length === 0) {
            location.reload(); // Reload to show empty cart state
        }
    }

    // Sync cart with server when user logs in
    syncCartOnLogin() {
        // Check if user just logged in and has cart data to sync
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('login') === 'success' && this.getCart().length > 0) {
            this.syncCartWithServer();
        }
    }

    // Sync localStorage cart with server
    syncCartWithServer() {
        const cart = this.getCart();
        if (cart.length === 0) return;

        fetch('/orders/cart/sync/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: `cart_data=${encodeURIComponent(JSON.stringify(cart))}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.clearCart();
                this.showToast('تم مزامنة سلة التسوق مع حسابك');
                setTimeout(() => location.reload(), 1000);
            }
        })
        .catch(error => {
            console.error('Error syncing cart:', error);
        });
    }

    // Get CSRF token
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Show toast message
    showToast(message) {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #22c55e;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 1000;
            font-weight: 500;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize cart manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.cartManager = new CartManager();
});