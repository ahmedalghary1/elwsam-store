// Wishlist functionality for guest users using localStorage
class WishlistManager {
    constructor() {
        this.wishlistKey = 'noor_wishlist';
        this.init();
    }

    init() {
        // Sync wishlist with server when user logs in
        this.syncWishlistOnLogin();

        // Update wishlist badge on page load
        this.updateWishlistBadge();

        // Handle add to wishlist buttons
        this.bindAddToWishlistButtons();

        // Handle remove from wishlist buttons
        this.bindRemoveFromWishlistButtons();

        // Handle wishlist page functionality
        this.initWishlistPage();
    }

    // Get wishlist from localStorage
    getWishlist() {
        try {
            return JSON.parse(localStorage.getItem(this.wishlistKey) || '[]');
        } catch (e) {
            return [];
        }
    }

    // Save wishlist to localStorage
    saveWishlist(wishlist) {
        localStorage.setItem(this.wishlistKey, JSON.stringify(wishlist));
        this.updateWishlistBadge();
    }

    // Add item to wishlist
    addToWishlist(productId, productData = {}) {
        const wishlist = this.getWishlist();

        if (!wishlist.includes(productId)) {
            wishlist.push(productId);
            this.saveWishlist(wishlist);
            this.showToast('تم إضافة المنتج للمفضلة');
            return true;
        } else {
            this.showToast('المنتج موجود بالفعل في المفضلة');
            return false;
        }
    }

    // Remove item from wishlist
    removeFromWishlist(productId) {
        const wishlist = this.getWishlist().filter(id => id != productId);
        this.saveWishlist(wishlist);
        this.showToast('تم حذف المنتج من المفضلة');
    }

    // Check if product is in wishlist
    isInWishlist(productId) {
        return this.getWishlist().includes(productId);
    }

    // Get wishlist count
    getWishlistCount() {
        return this.getWishlist().length;
    }

    // Clear wishlist
    clearWishlist() {
        this.saveWishlist([]);
    }

    // Update wishlist badge in navbar
    updateWishlistBadge() {
        const isAuthenticated = document.querySelector('[data-authenticated="true"]') !== null;
        let count = 0;

        if (isAuthenticated) {
            // For authenticated users, use server data (context processor)
            const badge = document.querySelector('.wishlist-count');
            if (badge && badge.textContent) {
                count = parseInt(badge.textContent) || 0;
            }
        } else {
            // For guest users, use localStorage
            count = this.getWishlistCount();
        }

        document.querySelectorAll('.wishlist-count').forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        });

        // Update heart icons
        document.querySelectorAll('[data-action="add-to-wishlist"]').forEach(btn => {
            const productId = btn.dataset.productId;
            const icon = btn.querySelector('i');
            if (icon) {
                if (this.isInWishlist(productId)) {
                    icon.className = 'fas fa-heart';
                    btn.classList.add('active');
                } else {
                    icon.className = 'far fa-heart';
                    btn.classList.remove('active');
                }
            }
        });
    }

    // Bind remove from wishlist buttons
    bindRemoveFromWishlistButtons() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-action="remove-from-wishlist"]');
            if (!button) return;

            e.preventDefault();

            const productId = button.dataset.productId;

            // Check if user is authenticated
            const isAuthenticated = document.querySelector('[data-authenticated="true"]') !== null;

            if (isAuthenticated) {
                // User is logged in, use AJAX
                this.removeFromWishlistAjax(productId, button);
            } else {
                // User is not logged in, use localStorage
                this.removeFromWishlist(productId);
                // Remove the item from DOM
                button.closest('.wishlist-item').remove();
                this.checkEmptyWishlist();
            }
        });
    }

    // Add to wishlist via AJAX (for authenticated users)
    addToWishlistAjax(productId, button) {
        fetch(`/orders/wishlist/add-ajax/${productId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message);
                if (data.action === 'added') {
                    // Update button appearance
                    const icon = button.querySelector('i');
                    if (icon) {
                        icon.className = 'fas fa-heart';
                        button.classList.add('active');
                    }
                }
            } else {
                if (data.login_required) {
                    // Redirect to login
                    window.location.href = '/accounts/login/';
                } else {
                    this.showToast(data.message);
                }
            }
        })
        .catch(error => {
            console.error('Error adding to wishlist:', error);
            this.showToast('حدث خطأ أثناء إضافة المنتج للمفضلة');
        });
    }

    // Remove from wishlist via AJAX (for authenticated users)
    removeFromWishlistAjax(productId, button) {
        fetch(`/orders/wishlist/remove-ajax/${productId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast(data.message);
                // Remove the item from DOM
                button.closest('.wishlist-item').remove();
                this.checkEmptyWishlist();
            } else {
                this.showToast(data.message);
            }
        })
        .catch(error => {
            console.error('Error removing from wishlist:', error);
            this.showToast('حدث خطأ أثناء حذف المنتج من المفضلة');
        });
    }

    // Initialize wishlist page functionality
    initWishlistPage() {
        if (!document.querySelector('.wishlist-page')) return;

        this.renderWishlistPage();
        this.bindWishlistPageEvents();
    }

    // Render wishlist items on wishlist page
    renderWishlistPage() {
        const wishlist = this.getWishlist();
        const wishlistContainer = document.querySelector('.wishlist-items');

        if (!wishlistContainer) return;

        if (wishlist.length === 0) {
            // Show empty wishlist
            document.querySelector('.wishlist-page').innerHTML = `
                <div class="container">
                    <div class="empty-wishlist">
                        <div class="empty-wishlist-icon">
                            <i class="fas fa-heart"></i>
                        </div>
                        <h2>المفضلة فارغة</h2>
                        <p>لم تقم بإضافة أي منتجات للمفضلة بعد</p>
                        <a href="{% url 'products:product_list' %}" class="btn btn-primary">تصفح المنتجات</a>
                    </div>
                </div>
            `;
            return;
        }

        // For guest users, show basic structure (would need server data for full details)
        wishlistContainer.innerHTML = wishlist.map(productId => `
            <div class="wishlist-item" data-product-id="${productId}">
                <div class="item-details">
                    <h3>منتج رقم ${productId}</h3>
                    <p>سيتم تحميل تفاصيل المنتج عند تسجيل الدخول</p>
                </div>
                <div class="item-actions">
                    <button class="remove-btn" data-product-id="${productId}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Bind wishlist page events
    bindWishlistPageEvents() {
        // Remove buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.remove-btn');
            if (!btn) return;

            if (confirm('هل أنت متأكد من حذف هذا المنتج من المفضلة؟')) {
                const productId = btn.dataset.productId;
                this.removeFromWishlist(productId);
                btn.closest('.wishlist-item').remove();
                this.checkEmptyWishlist();
            }
        });
    }

    // Check if wishlist is empty
    checkEmptyWishlist() {
        const items = document.querySelectorAll('.wishlist-item');
        if (items.length === 0) {
            location.reload(); // Reload to show empty wishlist state
        }
    }

    // Sync wishlist with server when user logs in
    syncWishlistOnLogin() {
        // Check if user just logged in and has wishlist data to sync
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('login') === 'success' && this.getWishlist().length > 0) {
            this.syncWishlistWithServer();
        }
    }

    // Sync localStorage wishlist with server
    syncWishlistWithServer() {
        const wishlist = this.getWishlist();
        if (wishlist.length === 0) return;

        fetch('/orders/wishlist/sync/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: `wishlist_data=${encodeURIComponent(JSON.stringify(wishlist))}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.clearWishlist();
                this.showToast('تم مزامنة المفضلة مع حسابك');
                setTimeout(() => location.reload(), 1000);
            }
        })
        .catch(error => {
            console.error('Error syncing wishlist:', error);
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

// Initialize wishlist manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.wishlistManager = new WishlistManager();
});