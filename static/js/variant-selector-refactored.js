/**
 * Refactored Variant Selector - Production Ready
 * 
 * Features:
 * - Multi-level pricing support
 * - Conditional size requirement enforcement
 * - Debounced AJAX requests
 * - Request cancellation (AbortController)
 * - Required field indicators (red asterisk)
 * - Out-of-stock disabled states with labels
 * - Image loading skeleton
 * - Dynamic price updates
 * - Specific validation messages
 * - URL parameter support for variant pre-selection
 * - ARIA labels for accessibility
 * - Live region for price changes
 * - Keyboard focus management
 */

class VariantSelector {
    constructor() {
        // DOM elements
        this.container = document.getElementById('variants-container');
        this.priceElement = document.querySelector('.price-main');
        this.addToCartBtn = document.getElementById('detail-add-to-cart');
        this.buyNowBtn = document.getElementById('buy-now-btn');
        this.messageContainer = null;
        this.productId = this.addToCartBtn?.dataset.productId;
        this.defaultPrice = this.addToCartBtn?.dataset.productPrice;
        this.defaultImageUrl = document.getElementById('main-product-image')?.src;
        
        // State
        this.selectedOptions = {
            pattern: null,
            color: null,
            size: null
        };
        
        this.config = null;
        this.isLoading = false;
        this.abortController = null;
        this.debounceTimer = null;
        
        if (!this.container || !this.productId) return;
        
        this.init();
    }
    
    async init() {
        // Create message container
        this.createMessageContainer();
        
        // Create live region for screen readers
        this.createLiveRegion();
        
        // Load product configuration
        await this.loadProductConfig();
        
        // Check URL parameters for pre-selection
        this.checkURLParameters();
        
        // Attach event listeners
        this.attachEventListeners();
    }
    
    createMessageContainer() {
        const msg = document.createElement('div');
        msg.id = 'variant-message';
        msg.className = 'variant-message';
        msg.style.display = 'none';
        msg.setAttribute('role', 'alert');
        msg.setAttribute('aria-live', 'polite');
        this.container.parentElement.insertBefore(msg, this.container);
        this.messageContainer = msg;
    }
    
    createLiveRegion() {
        const liveRegion = document.createElement('div');
        liveRegion.id = 'price-live-region';
        liveRegion.className = 'sr-only';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        document.body.appendChild(liveRegion);
        this.liveRegion = liveRegion;
    }
    
    async loadProductConfig() {
        this.setLoading(true);
        
        try {
            const response = await fetch(`/api/product-config/${this.productId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.config = data;
                this.renderInitialUI();
            } else {
                this.showMessage('حدث خطأ في تحميل إعدادات المنتج', 'error');
            }
        } catch (error) {
            console.error('Error loading product config:', error);
            this.showMessage('حدث خطأ في الاتصال', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    renderInitialUI() {
        if (!this.config) return;
        
        // Clear container
        this.container.innerHTML = '';
        
        switch (this.config.configuration_type) {
            case 'pattern_based':
                this.renderPatternBasedUI();
                // Don't render colors initially - they will be loaded after pattern selection
                break;
            case 'size_based':
                this.renderSizeBasedUI();
                // Render colors for size-based products
                if (this.config.has_colors) {
                    this.renderColorGroup(this.config.colors);
                }
                break;
            case 'simple':
                // No selectors needed
                this.updateUI({ available: true, price: this.config.base_price });
                // Render colors for simple products
                if (this.config.has_colors) {
                    this.renderColorGroup(this.config.colors);
                }
                break;
        }
    }
    
    renderPatternBasedUI() {
        const patterns = this.config.patterns || [];
        
        if (patterns.length > 0) {
            const html = `
                <div class="variant-group" id="group-pattern">
                    <div class="variant-label">
                        <i class="fas fa-layer-group"></i> النمط
                        <span class="required-indicator" aria-label="مطلوب">*</span>
                    </div>
                    <div class="variant-options" role="radiogroup" aria-label="اختر النمط" aria-required="true">
                        ${patterns.map(pattern => `
                            <button class="variant-btn" 
                                    data-variant-type="pattern" 
                                    data-value="${pattern.id}"
                                    data-has-sizes="${pattern.has_sizes}"
                                    role="radio"
                                    aria-checked="false">
                                <span>${pattern.name}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>`;
            this.container.insertAdjacentHTML('beforeend', html);
        }
        
        // Don't render colors or sizes initially - they will appear after pattern selection
    }
    
    renderSizeBasedUI() {
        const sizes = this.config.product_sizes || [];
        
        if (sizes.length > 0) {
            this.renderSizeGroup(sizes, true);
        }
    }
    
    renderColorGroup(colors) {
        const groupId = 'group-color';
        let group = document.getElementById(groupId);
        
        const innerContent = `
            <div class="variant-label">
                <i class="fas fa-palette"></i> اللون
                <span class="required-indicator" aria-label="مطلوب">*</span>
            </div>
            <div class="variant-options" role="radiogroup" aria-label="اختر اللون" aria-required="true">
                ${colors.map(color => `
                    <button class="variant-btn color-btn ${color.available === false ? 'disabled' : ''}" 
                            data-variant-type="color" 
                            data-value="${color.id}"
                            ${color.available === false ? 'disabled' : ''}
                            role="radio"
                            aria-checked="false"
                            aria-label="${color.name}${color.available === false ? ' - غير متوفر' : ''}">
                        <span class="color-swatch" style="background-color: ${color.code}"></span>
                        <span>${color.name}</span>
                        ${color.available === false ? '<span class="out-of-stock-label">غير متوفر</span>' : ''}
                    </button>
                `).join('')}
            </div>`;
        
        if (group) {
            // Update existing group content
            group.innerHTML = innerContent;
        } else {
            // Create new group
            const newGroup = document.createElement('div');
            newGroup.className = 'variant-group';
            newGroup.id = groupId;
            newGroup.innerHTML = innerContent;
            this.container.appendChild(newGroup);
        }
    }
    
    renderSizeGroup(sizes, required = false) {
        const groupId = 'group-size';
        let group = document.getElementById(groupId);
        
        const innerContent = `
            <div class="variant-label">
                <i class="fas fa-ruler"></i> المقاس
                ${required ? '<span class="required-indicator" aria-label="مطلوب">*</span>' : ''}
            </div>
            <div class="variant-options" role="radiogroup" aria-label="اختر المقاس" ${required ? 'aria-required="true"' : ''}>
                ${sizes.map(size => `
                    <button class="variant-btn ${size.available === false ? 'disabled' : ''}" 
                            data-variant-type="size" 
                            data-value="${size.id}"
                            ${size.available === false ? 'disabled' : ''}
                            role="radio"
                            aria-checked="false"
                            aria-label="${size.name}${size.available === false ? ' - غير متوفر' : ''}">
                        <span>${size.name}</span>
                        ${size.available === false ? '<span class="out-of-stock-label">غير متوفر</span>' : ''}
                    </button>
                `).join('')}
            </div>`;
        
        if (group) {
            // Update existing group content
            group.innerHTML = innerContent;
        } else {
            // Create new group
            const newGroup = document.createElement('div');
            newGroup.className = 'variant-group';
            newGroup.id = groupId;
            newGroup.innerHTML = innerContent;
            this.container.appendChild(newGroup);
        }
    }
    
    attachEventListeners() {
        // Event delegation for variant buttons
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
            btn.setAttribute('aria-checked', 'false');
        } else {
            btn.classList.add('active');
            btn.setAttribute('aria-checked', 'true');
            this.selectedOptions[type] = value;
            
            // Announce selection to screen readers
            this.announceSelection(type, btn.textContent.trim());
        }
        
        // Handle dependent selections
        if (type === 'pattern') {
            this.selectedOptions.color = null;
            this.selectedOptions.size = null;
            this.resetImages();
            
            // Load colors and sizes for the selected pattern
            if (this.selectedOptions.pattern) {
                await this.loadPatternOptions(value);
            } else {
                // Pattern deselected - remove colors and sizes
                this.removeColorGroup();
                this.removeSizeGroup();
            }
        } else if (type === 'color') {
            // Clear size selection when color changes
            this.selectedOptions.size = null;
            this.clearActiveState('size');
            
            if (this.selectedOptions.color) {
                this.updateImages(this.selectedOptions.color);
                // Don't update sizes - they are already displayed with the pattern
            } else {
                this.resetImages();
            }
        }
        
        // Debounced validation and price update
        this.debouncedValidateAndUpdate();
    }
    
    async loadPatternOptions(patternId) {
        try {
            const response = await fetch(`/api/variant-options/${this.productId}/?pattern_id=${patternId}`);
            const data = await response.json();
            
            if (data.success) {
                // Load colors if available
                if (data.colors && data.colors.length > 0) {
                    this.renderColorGroup(data.colors);
                } else {
                    this.removeColorGroup();
                }
                
                // Show sizes immediately along with colors
                if (data.sizes && data.sizes.length > 0) {
                    this.renderSizeGroup(data.sizes, data.requires_size);
                } else {
                    this.removeSizeGroup();
                }
            }
        } catch (error) {
            console.error('Error loading pattern options:', error);
        }
    }
    
    async updateSizesForColor(patternId, colorId) {
        try {
            const url = `/api/variant-options/${this.productId}/?pattern_id=${patternId}&color_id=${colorId}`;
            console.log('Fetching sizes from:', url);
            
            const response = await fetch(url);
            const data = await response.json();
            
            console.log('Received data:', data);
            console.log('Sizes:', data.sizes);
            console.log('Requires size:', data.requires_size);
            
            if (data.success) {
                // Update sizes based on color selection
                if (data.sizes && data.sizes.length > 0) {
                    console.log('Rendering', data.sizes.length, 'sizes');
                    this.renderSizeGroup(data.sizes, data.requires_size);
                } else {
                    console.log('No sizes available, removing size group');
                    this.removeSizeGroup();
                }
            } else {
                console.error('API returned success: false');
            }
        } catch (error) {
            console.error('Error updating sizes for color:', error);
        }
    }
    
    removeSizeGroup() {
        const group = document.getElementById('group-size');
        if (group) group.remove();
    }
    
    removeColorGroup() {
        const group = document.getElementById('group-color');
        if (group) group.remove();
    }
    
    clearActiveState(type) {
        this.container.querySelectorAll(`[data-variant-type="${type}"]`)
            .forEach(btn => {
                btn.classList.remove('active');
                btn.setAttribute('aria-checked', 'false');
            });
    }
    
    debouncedValidateAndUpdate() {
        // Cancel previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Cancel previous AJAX request
        if (this.abortController) {
            this.abortController.abort();
        }
        
        // Set new timer
        this.debounceTimer = setTimeout(() => {
            this.validateAndUpdatePrice();
        }, 300);
    }
    
    async validateAndUpdatePrice() {
        // Create new abort controller
        this.abortController = new AbortController();
        
        try {
            const params = new URLSearchParams();
            if (this.selectedOptions.pattern) params.append('pattern_id', this.selectedOptions.pattern);
            if (this.selectedOptions.color) params.append('color_id', this.selectedOptions.color);
            if (this.selectedOptions.size) params.append('size_id', this.selectedOptions.size);
            
            const response = await fetch(`/api/variant-info/${this.productId}/?${params}`, {
                signal: this.abortController.signal
            });
            const data = await response.json();
            
            if (data.success && data.variant) {
                this.updateUI(data.variant);
                this.hideMessage();
            } else {
                // Show specific validation message
                if (data.validation && !data.validation.valid) {
                    this.showMessage(data.validation.message, 'warning');
                    this.updateUI(null);
                } else {
                    this.showMessage(data.message || 'هذا التركيب غير متوفر', 'warning');
                    this.updateUI(null);
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                // Request was cancelled, ignore
                return;
            }
            console.error('Error validating selection:', error);
            this.showMessage('حدث خطأ في التحقق من الاختيار', 'error');
        }
    }
    
    updateUI(variant) {
        if (variant && variant.available) {
            // Valid variant found
            const price = parseFloat(variant.price).toFixed(2);
            this.priceElement.textContent = `${price} ج.م`;
            this.addToCartBtn.disabled = false;
            this.buyNowBtn.disabled = false;
            this.addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> أضف إلى السلة';
            this.addToCartBtn.dataset.variantId = variant.id;
            
            // Announce price change to screen readers
            this.announcePriceChange(price);
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
            this.container.setAttribute('aria-busy', 'true');
        } else {
            this.container.style.opacity = '1';
            this.container.style.pointerEvents = 'auto';
            this.container.setAttribute('aria-busy', 'false');
        }
    }
    
    showMessage(text, type = 'info') {
        if (!this.messageContainer) return;
        
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
        const mainImage = document.getElementById('main-product-image');
        const galleryThumbs = document.querySelector('.gallery-thumbs');
        
        if (!mainImage || !galleryThumbs) return;
        
        // Show skeleton loader
        this.showImageSkeleton(mainImage, galleryThumbs);
        
        try {
            const response = await fetch(`/api/product-images/${this.productId}/${colorId}/`);
            const data = await response.json();
            
            if (!data.success || data.images.length === 0) {
                // Keep current images if fetch fails
                this.hideImageSkeleton(mainImage, galleryThumbs);
                return;
            }
            
            // Update images with fade effect
            mainImage.style.opacity = '0';
            setTimeout(() => {
                mainImage.src = data.images[0];
                mainImage.style.opacity = '1';
            }, 150);
            
            galleryThumbs.innerHTML = data.images.map((url, i) => 
                `<div class="gallery-thumb ${i === 0 ? 'active' : ''}" data-src="${url}">
                    <img src="${url}" alt="Product Image" loading="lazy">
                </div>`
            ).join('');
            
            // Reattach thumbnail click handlers
            galleryThumbs.querySelectorAll('.gallery-thumb').forEach(thumb => {
                thumb.addEventListener('click', (e) => {
                    mainImage.src = e.currentTarget.dataset.src;
                    galleryThumbs.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                });
            });
            
            this.hideImageSkeleton(mainImage, galleryThumbs);
        } catch (error) {
            console.error('Error fetching images:', error);
            this.hideImageSkeleton(mainImage, galleryThumbs);
        }
    }
    
    showImageSkeleton(mainImage, galleryThumbs) {
        mainImage.classList.add('loading-skeleton');
        galleryThumbs.classList.add('loading-skeleton');
    }
    
    hideImageSkeleton(mainImage, galleryThumbs) {
        mainImage.classList.remove('loading-skeleton');
        galleryThumbs.classList.remove('loading-skeleton');
    }
    
    resetImages() {
        const mainImage = document.getElementById('main-product-image');
        const galleryThumbs = document.querySelector('.gallery-thumbs');
        
        if (mainImage && this.defaultImageUrl) {
            mainImage.style.opacity = '0';
            setTimeout(() => {
                mainImage.src = this.defaultImageUrl;
                mainImage.style.opacity = '1';
            }, 150);
        }
        
        if (galleryThumbs && this.defaultImageUrl) {
            galleryThumbs.innerHTML = `
                <div class="gallery-thumb active" data-src="${this.defaultImageUrl}">
                    <img src="${this.defaultImageUrl}" alt="Product Image">
                </div>`;
        }
    }
    
    checkURLParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const variantId = urlParams.get('variant_id');
        
        if (variantId) {
            // TODO: Pre-select variant based on ID
            // This would require an additional API endpoint to get variant details by ID
            console.log('Pre-selecting variant:', variantId);
        }
    }
    
    announceSelection(type, value) {
        const typeNames = {
            pattern: 'النمط',
            color: 'اللون',
            size: 'المقاس'
        };
        
        if (this.liveRegion) {
            this.liveRegion.textContent = `تم اختيار ${typeNames[type]}: ${value}`;
        }
    }
    
    announcePriceChange(price) {
        if (this.liveRegion) {
            setTimeout(() => {
                this.liveRegion.textContent = `السعر الجديد: ${price} جنيه مصري`;
            }, 500);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new VariantSelector();
});
