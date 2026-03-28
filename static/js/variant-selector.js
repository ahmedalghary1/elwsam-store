document.addEventListener('DOMContentLoaded', function() {
    const variantsDataElement = document.getElementById('variants-data');
    if (!variantsDataElement) return;

    const variants = JSON.parse(variantsDataElement.textContent);
    if (variants.length === 0) return;

    const variantsContainer = document.getElementById('variants-container');
    const priceMain = document.querySelector('.price-main');
    const addToCartBtn = document.getElementById('detail-add-to-cart');
    const buyNowBtn = document.getElementById('buy-now-btn');
    const productId = addToCartBtn.dataset.productId;
    const defaultImageUrl = document.getElementById('main-product-image').src;

    let selectedOptions = {};

    const hasPatterns = variants.some(v => v.pattern__id);
    const hasColors = variants.some(v => v.color__id);
    const hasSizes = variants.some(v => v.size__id);

    const createOptionSelector = (name, options, title) => {
        const isColor = name === 'color__id';
        const icon = isColor ? 'fa-palette' : 'fa-tags';
        let optionsHtml = options.map(opt => {
            const colorSwatch = isColor ? `<span class="color-swatch" style="background-color: ${opt.code || '#ccc'}"></span>` : '';
            return `
                <button class="variant-btn ${isColor ? 'color-btn' : ''}" data-variant-type="${name}" data-value="${opt.id}">
                    ${colorSwatch}<span>${opt.name}</span>
                </button>`;
        }).join('');
        return `
            <div class="variant-group" id="group-${name}">
                <div class="variant-label"><i class="fas ${icon}"></i> ${title}</div>
                <div class="variant-options">${optionsHtml}</div>
            </div>`;
    };

    const renderNextLevel = (currentLevel) => {
        if (currentLevel === 'pattern__id') {
            variantsContainer.querySelector('#group-color__id')?.remove();
            variantsContainer.querySelector('#group-size__id')?.remove();
            if (hasColors) {
                const filtered = variants.filter(v => !hasPatterns || v.pattern__id === selectedOptions.pattern__id);
                const colors = [...new Map(filtered.map(v => [v.color__id, {id: v.color__id, name: v.color__name, code: v.color__code}])).values()].filter(c => c.id);
                if (colors.length) variantsContainer.insertAdjacentHTML('beforeend', createOptionSelector('color__id', colors, 'اللون'));
            } else {
                renderNextLevel('color__id');
            }
        }
        if (currentLevel === 'color__id') {
            variantsContainer.querySelector('#group-size__id')?.remove();
            if (hasSizes) {
                const filtered = variants.filter(v => 
                    (!hasPatterns || v.pattern__id === selectedOptions.pattern__id) &&
                    (!hasColors || v.color__id === selectedOptions.color__id)
                );
                const sizes = [...new Map(filtered.map(v => [v.size__id, {id: v.size__id, name: v.size__name}])).values()].filter(s => s.id);
                if (sizes.length) variantsContainer.insertAdjacentHTML('beforeend', createOptionSelector('size__id', sizes, 'المقاس'));
            }
        }
    };

    const updateUI = () => {
        const allRequiredSelected = (!hasPatterns || selectedOptions.pattern__id) && (!hasColors || selectedOptions.color__id) && (!hasSizes || selectedOptions.size__id);
        const variant = allRequiredSelected ? variants.find(v => 
            (!hasPatterns || v.pattern__id === selectedOptions.pattern__id) &&
            (!hasColors || v.color__id === selectedOptions.color__id) &&
            (!hasSizes || v.size__id === selectedOptions.size__id)
        ) : undefined;

        if (variant) {
            priceMain.textContent = `${parseFloat(variant.price).toFixed(2)} ج.م`;
            [addToCartBtn, buyNowBtn].forEach(btn => { btn.disabled = false; });
            addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> أضف إلى السلة';
        } else {
            [addToCartBtn, buyNowBtn].forEach(btn => { btn.disabled = true; });
            priceMain.textContent = document.getElementById('detail-add-to-cart').dataset.productPrice + ' ج.م';
            addToCartBtn.innerHTML = allRequiredSelected ? '<i class="fas fa-times-circle"></i> غير متاح' : '<i class="fas fa-check-square"></i> اختر الخيارات';
        }
    };

    const updateImages = (colorId) => {
        fetch(`/products/images/${productId}/${colorId}/`).then(r => r.json()).then(data => {
            if (!data.success || data.images.length === 0) {
                resetImages();
                return;
            }
            const mainImage = document.getElementById('main-product-image');
            const galleryThumbs = document.querySelector('.gallery-thumbs');
            mainImage.src = data.images[0];
            galleryThumbs.innerHTML = data.images.map((url, i) => `<div class="gallery-thumb ${i === 0 ? 'active' : ''}" data-src="${url}"><img src="${url}" alt="Product Image"></div>`).join('');
            galleryThumbs.querySelectorAll('.gallery-thumb').forEach(t => t.addEventListener('click', e => {
                mainImage.src = e.currentTarget.dataset.src;
                galleryThumbs.querySelectorAll('.gallery-thumb').forEach(th => th.classList.remove('active'));
                e.currentTarget.classList.add('active');
            }));
        }).catch(err => {
            console.error('Error fetching images:', err);
            resetImages();
        });
    };

    const resetImages = () => {
        const mainImage = document.getElementById('main-product-image');
        const galleryThumbs = document.querySelector('.gallery-thumbs');
        mainImage.src = defaultImageUrl;
        galleryThumbs.innerHTML = `<div class="gallery-thumb active" data-src="${defaultImageUrl}"><img src="${defaultImageUrl}" alt="Product Image"></div>`;
    };

    variantsContainer.addEventListener('click', e => {
        const target = e.target.closest('.variant-btn');
        if (!target) return;

        const type = target.dataset.variantType;
        const value = parseInt(target.dataset.value, 10);
        const wasActive = target.classList.contains('active');

        document.querySelectorAll(`.variant-btn[data-variant-type="${type}"]`).forEach(btn => btn.classList.remove('active'));

        if (wasActive) {
            delete selectedOptions[type];
        } else {
            target.classList.add('active');
            selectedOptions[type] = value;
        }
        
        if (type === 'pattern__id') {
            delete selectedOptions.color__id;
            delete selectedOptions.size__id;
            resetImages();
            renderNextLevel('pattern__id');
        } else if (type === 'color__id') {
            delete selectedOptions.size__id;
            if (selectedOptions.color__id) {
                updateImages(selectedOptions.color__id);
            } else {
                resetImages();
            }
            renderNextLevel('color__id');
        }

        updateUI();
    });

    // Initial Render
    if (hasPatterns) {
        const patterns = [...new Map(variants.map(v => [v.pattern__id, {id: v.pattern__id, name: v.pattern__name}])).values()].filter(p => p.id);
        variantsContainer.innerHTML = createOptionSelector('pattern__id', patterns, 'النمط');
    } else {
        renderNextLevel('pattern__id');
    }
    updateUI();
});
