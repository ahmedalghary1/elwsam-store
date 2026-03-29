/**
 * FLEXIBLE VARIANT SELECTOR - REDESIGNED SYSTEM
 * ==============================================
 * 
 * Supports:
 * - Simple products (no variants)
 * - Size-based products (product-level sizes)
 * - Pattern-based products (patterns with/without sizes)
 * - Conditional size requirements
 * - Multi-level pricing
 * 
 * Architecture:
 * - Event-driven with AJAX
 * - Backend-driven validation
 * - Dynamic UI updates
 * - Stock-aware filtering
 */

class FlexibleVariantSelector {
    constructor() {
        this.container = document.getElementById('variants-container');
        this.priceElement = document.querySelector('.price-main');
        this.addToCartBtn = document.getElementById('detail-add-to-cart');
        this.buyNowBtn = document.getElementById('buy-now-btn');
        this.productId = this.addToCartBtn?.dataset.productId;
        this.defaultPrice = this.addToCartBtn?.dataset.productPrice;
        
        // Product configuration (loaded from API)
        this.config = null;
        
        // Current selection state
        this.selection = {
            pattern: null,
            size: null,
            color: null
        };
        
        // Validation state
        this.validation = {
            valid: false,
            requiresSize: false,
            message: null
        };
        
        if (this.container && this.productId) {
            this.init();
        }
    }
    
    async init() {
        try {
            // Load product configuration
            await this.loadProductConfig();
            
            // Render initial UI based on configuration
            this.renderUI();
            
            // Attach event listeners
            this.attachEventListeners();
            
        } catch (error) {
            console.error('Failed to initialize variant selector:', error);
            this.showMessage('حدث خطأ في تحميل خيارات المنتج', 'error');
        }
    }
    
    async loadProductConfig() {
        this.setLoading(true);
        
        try {
            const response = await fetch(`/api/product-config/${this.productId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.config = data;
                console.log('Product configuration loaded:', this.config);
            } else {
                throw new Error(data.error || 'Failed to load configuration');
            }
        } finally {
            this.setLoading(false);
        }
    }
    
    renderUI() {
        if (!this.config) return;
        
        this.container.innerHTML = '';
        
        // Render based on configuration type
        switch (this.config.configuration_type) {
            case 'pattern_based':
                this.renderPatternSelector();
                break;
            
            case 'size_based':
                this.renderSizeSelector(this.config.product_sizes);
                break;
            
            case 'simple':
                // No variant selection needed
                this.updatePriceAndButton(this.config.base_price, true);
                break;
        }
        
        // Always render color selector if colors exist
        if (this.config.colors && this.config.colors.length > 0) {
            this.renderColorSelector();
        }
    }
    
    renderPatternSelector() {
        if (!this.config.patterns || this.config.patterns.length === 0) return;
        
        const group = document.createElement('div');
        group.className = 'variant-group';
        group.id = 'group-pattern';
        
        const label = document.createElement('div');
        label.className = 'variant-label';
        label.innerHTML = '<i class="fas fa-layer-group"></i> اختر النمط';
        
        const options = document.createElement('div');
        options.className = 'variant-options';
        
        this.config.patterns.forEach(pattern => {
            const btn = document.createElement('button');
            btn.className = 'variant-btn';
            btn.dataset.patternId = pattern.id;
            btn.dataset.hasSizes = pattern.has_sizes;
            btn.textContent = pattern.name;
            
            if (this.selection.pattern === pattern.id) {
                btn.classList.add('active');
            }
            
            options.appendChild(btn);
        });
        
        group.appendChild(label);
        group.appendChild(options);
        this.container.appendChild(group);
    }
    
    renderSizeSelector(sizes, patternContext = false) {
        if (!sizes || sizes.length === 0) return;
        
        // Remove existing size group
        const existingGroup = document.getElementById('group-size');
        if (existingGroup) {
            existingGroup.remove();
        }
        
        const group = document.createElement('div');
        group.className = 'variant-group';
        group.id = 'group-size';
        
        const label = document.createElement('div');
        label.className = 'variant-label';
        
        // Show required indicator if size is required
        const requiresSize = patternContext ? 
            this.getSelectedPattern()?.requires_size : 
            this.config.requires_size;
        
        label.innerHTML = `<i class="fas fa-ruler"></i> اختر المقاس ${requiresSize ? '<span style="color: red;">*</span>' : ''}`;
        
        const options = document.createElement('div');
        options.className = 'variant-options';
        
        sizes.forEach(size => {
            const btn = document.createElement('button');
            btn.className = 'variant-btn';
            btn.dataset.sizeId = size.id;
            btn.dataset.price = size.price;
            btn.textContent = size.name;
            
            if (this.selection.size === size.id) {
                btn.classList.add('active');
            }
            
            // Show price if different from base
            if (size.price && size.price !== this.config.base_price) {
                const priceSpan = document.createElement('span');
                priceSpan.style.fontSize = '0.85em';
                priceSpan.style.opacity = '0.8';
                priceSpan.textContent = ` (${parseFloat(size.price).toFixed(2)} ج.م)`;
                btn.appendChild(priceSpan);
            }
            
            options.appendChild(btn);
        });
        
        group.appendChild(label);
        group.appendChild(options);
        this.container.appendChild(group);
    }
    
    renderColorSelector() {
        // Remove existing color group
        const existingGroup = document.getElementById('group-color');
        if (existingGroup) {
            existingGroup.remove();
        }
        
        const group = document.createElement('div');
        group.className = 'variant-group';
        group.id = 'group-color';
        
        const label = document.createElement('div');
        label.className = 'variant-label';
        label.innerHTML = '<i class="fas fa-palette"></i> اختر اللون';
        
        const options = document.createElement('div');
        options.className = 'variant-options';
        
        this.config.colors.forEach(color => {
            const btn = document.createElement('button');
            btn.className = 'variant-btn color-btn';
            btn.dataset.colorId = color.id;
            
            const swatch = document.createElement('span');
            swatch.className = 'color-swatch';
            swatch.style.backgroundColor = color.code;
            
            btn.appendChild(swatch);
            btn.appendChild(document.createTextNode(color.name));
            
            if (this.selection.color === color.id) {
                btn.classList.add('active');
            }
            
            options.appendChild(btn);
        });
        
        group.appendChild(label);
        group.appendChild(options);
        this.container.appendChild(group);
    }
    
    attachEventListeners() {
        this.container.addEventListener('click', (e) => {
            const btn = e.target.closest('.variant-btn');
            if (!btn) return;
            
            // Determine option type
            if (btn.dataset.patternId) {
                this.handlePatternClick(btn);
            } else if (btn.dataset.sizeId) {
                this.handleSizeClick(btn);
            } else if (btn.dataset.colorId) {
                this.handleColorClick(btn);
            }
        });
    }
    
    async handlePatternClick(btn) {
        const patternId = parseInt(btn.dataset.patternId);
        const hasSizes = btn.dataset.hasSizes === 'true';
        
        // Toggle selection
        if (this.selection.pattern === patternId) {
            this.selection.pattern = null;
            this.selection.size = null; // Clear dependent selection
            btn.classList.remove('active');
        } else {
            // Deselect previous
            this.container.querySelectorAll('#group-pattern .variant-btn').forEach(b => {
                b.classList.remove('active');
            });
            
            this.selection.pattern = patternId;
            this.selection.size = null; // Clear size when pattern changes
            btn.classList.add('active');
        }
        
        // Update size selector based on pattern
        if (this.selection.pattern && hasSizes) {
            const pattern = this.getSelectedPattern();
            if (pattern && pattern.sizes) {
                this.renderSizeSelector(pattern.sizes, true);
            }
        } else {
            // Remove size selector if pattern doesn't have sizes
            const sizeGroup = document.getElementById('group-size');
            if (sizeGroup) {
                sizeGroup.remove();
            }
        }
        
        // Validate and update price
        await this.validateAndUpdatePrice();
    }
    
    async handleSizeClick(btn) {
        const sizeId = parseInt(btn.dataset.sizeId);
        
        // Toggle selection
        if (this.selection.size === sizeId) {
            this.selection.size = null;
            btn.classList.remove('active');
        } else {
            // Deselect previous
            this.container.querySelectorAll('#group-size .variant-btn').forEach(b => {
                b.classList.remove('active');
            });
            
            this.selection.size = sizeId;
            btn.classList.add('active');
        }
        
        // Validate and update price
        await this.validateAndUpdatePrice();
    }
    
    async handleColorClick(btn) {
        const colorId = parseInt(btn.dataset.colorId);
        
        // Toggle selection
        if (this.selection.color === colorId) {
            this.selection.color = null;
            btn.classList.remove('active');
        } else {
            // Deselect previous
            this.container.querySelectorAll('#group-color .variant-btn').forEach(b => {
                b.classList.remove('active');
            });
            
            this.selection.color = colorId;
            btn.classList.add('active');
        }
        
        // Update images if color changed
        if (this.selection.color) {
            await this.updateImages(this.selection.color);
        }
        
        // Validate and update price
        await this.validateAndUpdatePrice();
    }
    
    async validateAndUpdatePrice() {
        this.setLoading(true);
        
        try {
            const params = new URLSearchParams({
                product_id: this.productId
            });
            
            if (this.selection.pattern) params.append('pattern_id', this.selection.pattern);
            if (this.selection.size) params.append('size_id', this.selection.size);
            if (this.selection.color) params.append('color_id', this.selection.color);
            
            const response = await fetch(`/api/variant-price/?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.validation = data.validation;
                
                if (data.validation.valid) {
                    // Valid selection
                    this.updatePriceAndButton(data.price, data.available, data.variant_id);
                    this.clearMessage();
                } else {
                    // Invalid selection
                    this.updatePriceAndButton(this.defaultPrice, false);
                    
                    if (data.validation.message) {
                        this.showMessage(data.validation.message, 'warning');
                    }
                }
            }
        } catch (error) {
            console.error('Validation error:', error);
            this.showMessage('حدث خطأ في التحقق من الاختيار', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    updatePriceAndButton(price, available, variantId = null) {
        // Update price
        if (price) {
            this.priceElement.textContent = `${parseFloat(price).toFixed(2)} ج.م`;
        }
        
        // Update buttons
        if (available && variantId) {
            this.addToCartBtn.disabled = false;
            this.buyNowBtn.disabled = false;
            this.addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> أضف إلى السلة';
            this.addToCartBtn.dataset.variantId = variantId;
        } else {
            this.addToCartBtn.disabled = true;
            this.buyNowBtn.disabled = true;
            
            if (this.validation.requiresSize) {
                this.addToCartBtn.innerHTML = '<i class="fas fa-check-square"></i> اختر المقاس';
            } else if (!this.validation.valid) {
                this.addToCartBtn.innerHTML = '<i class="fas fa-check-square"></i> اختر الخيارات';
            } else {
                this.addToCartBtn.innerHTML = '<i class="fas fa-times-circle"></i> غير متاح';
            }
            
            delete this.addToCartBtn.dataset.variantId;
        }
    }
    
    async updateImages(colorId) {
        try {
            const response = await fetch(`/api/product-images/${this.productId}/${colorId}/`);
            const data = await response.json();
            
            if (data.success && data.images && data.images.length > 0) {
                const mainImage = document.getElementById('main-product-image');
                if (mainImage) {
                    mainImage.src = data.images[0];
                }
                
                // Update gallery thumbnails if they exist
                const gallery = document.querySelector('.gallery-thumbs');
                if (gallery) {
                    gallery.innerHTML = '';
                    data.images.forEach((imgUrl, index) => {
                        const thumb = document.createElement('img');
                        thumb.src = imgUrl;
                        thumb.className = 'gallery-thumb';
                        if (index === 0) thumb.classList.add('active');
                        gallery.appendChild(thumb);
                    });
                }
            }
        } catch (error) {
            console.error('Failed to update images:', error);
        }
    }
    
    getSelectedPattern() {
        if (!this.selection.pattern || !this.config.patterns) return null;
        return this.config.patterns.find(p => p.id === this.selection.pattern);
    }
    
    setLoading(loading) {
        if (loading) {
            this.container.classList.add('loading');
        } else {
            this.container.classList.remove('loading');
        }
    }
    
    showMessage(text, type = 'info') {
        this.clearMessage();
        
        const message = document.createElement('div');
        message.className = `variant-message variant-message-${type}`;
        message.textContent = text;
        message.id = 'variant-message';
        
        this.container.insertBefore(message, this.container.firstChild);
    }
    
    clearMessage() {
        const existing = document.getElementById('variant-message');
        if (existing) {
            existing.remove();
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new FlexibleVariantSelector();
});
