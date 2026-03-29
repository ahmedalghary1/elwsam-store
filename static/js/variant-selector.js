/**
 * Variant Selector - Refactored with Event-Driven Architecture
 * Features: AJAX-based option loading, loading states, smooth UX
 */

class VariantSelector {
    constructor() {
        this.container = document.getElementById('variants-container');
        this.priceElement = document.querySelector('.price-main');
        this.addToCartBtn = document.getElementById('detail-add-to-cart');
        this.buyNowBtn = document.getElementById('buy-now-btn');
        this.messageContainer = document.getElementById('variant-message');
        this.productId = this.addToCartBtn?.dataset.productId;
        this.defaultPrice = this.addToCartBtn?.dataset.productPrice;
        this.defaultImageUrl = document.getElementById('main-product-image')?.src;
        
        this.selectedOptions = {
            pattern: null,
            color: null,
            size: null
        };
        
        this.isLoading = false;
        
        if (!this.container || !this.productId) return;
        
        this.init();
    }
    
    init() {
        this.loadInitialOptions();
        this.attachEventListeners();
    }
    
    async loadInitialOptions() {
        await this.fetchOptions();
    }
    
    attachEventListeners() {
        this.container.addEventListener('click', (e) => {
            const btn = e.target.closest('.variant-btn');
            if (!btn || btn.disabled) return;
            
            const type = btn.dataset.variantType;
            const value = parseInt(btn.dataset.value, 10);
            
            this.handleOptionClick(type, value, btn);
        });
    }
    
    async handleOptionClick(type, value, btn) {
        const wasActive = btn.classList.contains('active');
        
        // Update selection
        this.clearActiveState(type);
        
        if (wasActive) {
            this.selectedOptions[type] = null;
        } else {
            btn.classList.add('active');
            this.selectedOptions[type] = value;
        }
        
        // Clear dependent selections
        if (type === 'pattern') {
            this.selectedOptions.color = null;
            this.selectedOptions.size = null;
            this.resetImages();
        } else if (type === 'color') {
            this.selectedOptions.size = null;
            if (this.selectedOptions.color) {
                this.updateImages(this.selectedOptions.color);
            } else {
                this.resetImages();
            }
        }
        
        // Fetch updated options
        await this.fetchOptions();
        
        // Update variant info if all required selections are made
        if (this.selectedOptions.color) {
            await this.fetchVariantInfo();
        } else {
            this.updateUI(null);
        }
    }
    
    clearActiveState(type) {
        this.container.querySelectorAll(`[data-variant-type="${type}"]`)
            .forEach(btn => btn.classList.remove('active'));
    }
    
    async fetchOptions() {
        if (this.isLoading) return;
        
        this.setLoading(true);
        
        try {
            const params = new URLSearchParams();
            if (this.selectedOptions.pattern) params.append('pattern_id', this.selectedOptions.pattern);
            if (this.selectedOptions.color) params.append('color_id', this.selectedOptions.color);
            
            const response = await fetch(`/api/variant-options/${this.productId}/?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderOptions(data);
            } else {
                this.showMessage('حدث خطأ في تحميل الخيارات', 'error');
            }
        } catch (error) {
            console.error('Error fetching options:', error);
            this.showMessage('حدث خطأ في الاتصال', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    async fetchVariantInfo() {
        try {
            const params = new URLSearchParams();
            if (this.selectedOptions.pattern) params.append('pattern_id', this.selectedOptions.pattern);
            if (this.selectedOptions.color) params.append('color_id', this.selectedOptions.color);
            if (this.selectedOptions.size) params.append('size_id', this.selectedOptions.size);
            
            const response = await fetch(`/api/variant-info/${this.productId}/?${params}`);
            const data = await response.json();
            
            if (data.success && data.variant) {
                this.updateUI(data.variant);
                this.hideMessage();
            } else {
                this.updateUI(null);
                if (this.selectedOptions.size) {
                    this.showMessage('هذا التركيب غير متوفر. الرجاء اختيار خيارات أخرى.', 'warning');
                }
            }
        } catch (error) {
            console.error('Error fetching variant info:', error);
        }
    }
    
    renderOptions(data) {
        // Render patterns (only initially)
        if (data.patterns && data.patterns.length > 0 && !this.selectedOptions.pattern) {
            this.renderGroup('pattern', data.patterns, 'النمط', 'fa-layer-group');
        }
        
        // Render colors
        if (data.has_colors) {
            this.updateGroup('color', data.colors, 'اللون', 'fa-palette');
        } else {
            this.removeGroup('color');
        }
        
        // Render sizes
        if (data.has_sizes) {
            this.updateGroup('size', data.sizes, 'المقاس', 'fa-ruler');
        } else {
            this.removeGroup('size');
        }
    }
    
    renderGroup(type, options, title, icon) {
        const groupId = `group-${type}`;
        let group = document.getElementById(groupId);
        
        if (!group) {
            const html = this.createGroupHTML(type, options, title, icon);
            this.container.insertAdjacentHTML('beforeend', html);
        }
    }
    
    updateGroup(type, options, title, icon) {
        const groupId = `group-${type}`;
        let group = document.getElementById(groupId);
        
        if (group) {
            // Update existing group
            const optionsContainer = group.querySelector('.variant-options');
            optionsContainer.innerHTML = this.createOptionsHTML(type, options);
            
            // Restore active state
            if (this.selectedOptions[type]) {
                const activeBtn = optionsContainer.querySelector(`[data-value="${this.selectedOptions[type]}"]`);
                if (activeBtn) activeBtn.classList.add('active');
            }
        } else {
            // Create new group
            const html = this.createGroupHTML(type, options, title, icon);
            this.container.insertAdjacentHTML('beforeend', html);
            
            // Set active state
            if (this.selectedOptions[type]) {
                const activeBtn = this.container.querySelector(`[data-variant-type="${type}"][data-value="${this.selectedOptions[type]}"]`);
                if (activeBtn) activeBtn.classList.add('active');
            }
        }
    }
    
    removeGroup(type) {
        const group = document.getElementById(`group-${type}`);
        if (group) group.remove();
    }
    
    createGroupHTML(type, options, title, icon) {
        return `
            <div class="variant-group" id="group-${type}">
                <div class="variant-label"><i class="fas ${icon}"></i> ${title}</div>
                <div class="variant-options">
                    ${this.createOptionsHTML(type, options)}
                </div>
            </div>`;
    }
    
    createOptionsHTML(type, options) {
        const isColor = type === 'color';
        return options.map(opt => {
            const colorSwatch = isColor ? `<span class="color-swatch" style="background-color: ${opt.code || '#ccc'}"></span>` : '';
            const isActive = this.selectedOptions[type] === opt.id ? 'active' : '';
            return `
                <button class="variant-btn ${isColor ? 'color-btn' : ''} ${isActive}" 
                        data-variant-type="${type}" 
                        data-value="${opt.id}">
                    ${colorSwatch}<span>${opt.name}</span>
                </button>`;
        }).join('');
    }
    
    updateUI(variant) {
        if (variant && variant.available) {
            // Valid variant found
            this.priceElement.textContent = `${parseFloat(variant.price).toFixed(2)} ج.م`;
            this.addToCartBtn.disabled = false;
            this.buyNowBtn.disabled = false;
            this.addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> أضف إلى السلة';
            this.addToCartBtn.dataset.variantId = variant.id;
        } else {
            // No valid variant or incomplete selection
            this.addToCartBtn.disabled = true;
            this.buyNowBtn.disabled = true;
            this.priceElement.textContent = `${this.defaultPrice} ج.م`;
            
            const hasAnySelection = this.selectedOptions.pattern || this.selectedOptions.color || this.selectedOptions.size;
            this.addToCartBtn.innerHTML = hasAnySelection && variant === null 
                ? '<i class="fas fa-times-circle"></i> غير متاح' 
                : '<i class="fas fa-check-square"></i> اختر الخيارات';
            
            delete this.addToCartBtn.dataset.variantId;
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        this.container.classList.toggle('loading', loading);
        
        if (loading) {
            this.container.style.opacity = '0.6';
            this.container.style.pointerEvents = 'none';
        } else {
            this.container.style.opacity = '1';
            this.container.style.pointerEvents = 'auto';
        }
    }
    
    showMessage(text, type = 'info') {
        if (!this.messageContainer) {
            const msg = document.createElement('div');
            msg.id = 'variant-message';
            msg.className = `variant-message variant-message-${type}`;
            this.container.parentElement.insertBefore(msg, this.container);
            this.messageContainer = msg;
        }
        
        this.messageContainer.textContent = text;
        this.messageContainer.className = `variant-message variant-message-${type}`;
        this.messageContainer.style.display = 'block';
    }
    
    hideMessage() {
        if (this.messageContainer) {
            this.messageContainer.style.display = 'none';
        }
    }
    
    async updateImages(colorId) {
        try {
            const response = await fetch(`/api/product-images/${this.productId}/${colorId}/`);
            const data = await response.json();
            
            if (!data.success || data.images.length === 0) {
                this.resetImages();
                return;
            }
            
            const mainImage = document.getElementById('main-product-image');
            const galleryThumbs = document.querySelector('.gallery-thumbs');
            
            mainImage.src = data.images[0];
            galleryThumbs.innerHTML = data.images.map((url, i) => 
                `<div class="gallery-thumb ${i === 0 ? 'active' : ''}" data-src="${url}">
                    <img src="${url}" alt="Product Image">
                </div>`
            ).join('');
            
            galleryThumbs.querySelectorAll('.gallery-thumb').forEach(thumb => {
                thumb.addEventListener('click', (e) => {
                    mainImage.src = e.currentTarget.dataset.src;
                    galleryThumbs.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                });
            });
        } catch (error) {
            console.error('Error fetching images:', error);
            this.resetImages();
        }
    }
    
    resetImages() {
        const mainImage = document.getElementById('main-product-image');
        const galleryThumbs = document.querySelector('.gallery-thumbs');
        
        if (mainImage && this.defaultImageUrl) {
            mainImage.src = this.defaultImageUrl;
        }
        
        if (galleryThumbs && this.defaultImageUrl) {
            galleryThumbs.innerHTML = `
                <div class="gallery-thumb active" data-src="${this.defaultImageUrl}">
                    <img src="${this.defaultImageUrl}" alt="Product Image">
                </div>`;
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new VariantSelector();
});
