/* ============================================
   متجر نور - Main JavaScript
   Vanilla JS - No Dependencies
   ============================================ */

'use strict';

function runWhenIdle(callback, timeout = 1500) {
  const run = () => {
    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(callback, { timeout });
    } else {
      window.setTimeout(callback, 0);
    }
  };

  if (document.readyState === 'complete') {
    run();
  } else {
    window.addEventListener('load', run, { once: true });
  }
}

// ============ Store (State) ============
const Store = {
  cart: JSON.parse(localStorage.getItem('noor_cart') || '[]'),
  wishlistItems: JSON.parse(localStorage.getItem('noor_wishlist_items') || '[]'),
  wishlistIds: JSON.parse(localStorage.getItem('noor_wishlist') || '[]'),

  saveCart() {
    localStorage.setItem('noor_cart', JSON.stringify(this.cart));
    UI.updateCartBadge();
  },
  saveWishlist() {
    localStorage.setItem('noor_wishlist', JSON.stringify(this.wishlistIds));
    localStorage.setItem('noor_wishlist_items', JSON.stringify(this.wishlistItems));
    UI.updateWishlistBadge();
  },
  addToCart(product) {
    const ex = this.cart.find(i => i.id === product.id);
    if (ex) { ex.qty++; } else { this.cart.push({ ...product, qty: 1 }); }
    this.saveCart();
  },
  removeFromCart(id) { this.cart = this.cart.filter(i => i.id !== id); this.saveCart(); },
  updateQty(id, delta) {
    const item = this.cart.find(i => i.id === id);
    if (item) { item.qty = Math.max(1, item.qty + delta); this.saveCart(); }
  },
  getCartTotal() { return this.cart.reduce((s, i) => s + i.price * i.qty, 0); },
  getCartCount() { return this.cart.reduce((s, i) => s + i.qty, 0); },
  toggleWishlist(id, productData) {
    const idx = this.wishlistIds.indexOf(id);
    if (idx === -1) {
      this.wishlistIds.push(id);
      if (productData && !this.wishlistItems.find(p => p.id === id)) {
        this.wishlistItems.push({ ...productData, addedAt: Date.now() });
      }
    } else {
      this.wishlistIds.splice(idx, 1);
      this.wishlistItems = this.wishlistItems.filter(p => p.id !== id);
    }
    this.saveWishlist();
    return idx === -1;
  },
  removeFromWishlist(id) {
    this.wishlistIds = this.wishlistIds.filter(i => i !== id);
    this.wishlistItems = this.wishlistItems.filter(p => p.id !== id);
    this.saveWishlist();
  },
  isWishlisted(id) { return this.wishlistIds.includes(id); }
};

// ============ UI ============
const UI = {
  toastTimer: null,
  showToast(message, icon = '✅') {
    let t = document.getElementById('noor-toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'noor-toast';
      t.className = 'toast';
      document.body.appendChild(t);
    }
    t.innerHTML = `<span>${icon}</span> ${message}`;
    t.classList.add('show');
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => t.classList.remove('show'), 3000);
  },
  updateCartBadge() {
    const isAuthenticated = document.querySelector('[data-authenticated="true"]') !== null;
    let count = 0;

    if (isAuthenticated) {
      // For authenticated users, use server data (context processor)
      const badge = document.querySelector('.cart-count');
      if (badge && badge.textContent) {
        count = parseInt(badge.textContent) || 0;
      }
    } else {
      // For guest users, use localStorage
      count = Store.getCartCount();
    }

    document.querySelectorAll('.cart-count').forEach(el => {
      el.textContent = count;
      el.style.display = count > 0 ? 'flex' : 'none';
    });
  },
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
      count = Store.wishlistIds.length;
    }

    document.querySelectorAll('.wishlist-count').forEach(el => {
      el.textContent = count;
      el.style.display = count > 0 ? 'flex' : 'none';
    });
  },
  formatPrice(p) { return Number(p).toLocaleString('ar-SA') + ' ج.م'; }
};
window.UI = UI;

// ============ Mobile Menu ============
const MobileMenu = {
  init() {
    const overlay = document.querySelector('.mobile-menu-overlay');
    const menu = document.querySelector('.mobile-menu');
    const hamburger = document.querySelector('.hamburger-btn');
    const closeBtn = document.querySelector('.mobile-menu-close');
    const open = () => { menu?.classList.add('open'); overlay?.classList.add('open'); hamburger?.classList.add('active'); hamburger?.setAttribute('aria-expanded','true'); document.body.style.overflow = 'hidden'; };
    const close = () => { menu?.classList.remove('open'); overlay?.classList.remove('open'); hamburger?.classList.remove('active'); hamburger?.setAttribute('aria-expanded','false'); document.body.style.overflow = ''; };
    hamburger?.addEventListener('click', () => menu?.classList.contains('open') ? close() : open());
    closeBtn?.addEventListener('click', close);
    overlay?.addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }
};

// ============ Search Overlay ============
function initSearch() {
  if (!document.getElementById('searchOverlay')) {
    const el = document.createElement('div');
    el.id = 'searchOverlay';
    el.className = 'search-overlay';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-hidden', 'true');
    el.innerHTML = `<form class="search-overlay-box" id="searchOverlayForm" role="search"><div class="search-overlay-input-wrap"><span style="font-size:1.2rem" aria-hidden="true">🔍</span><input type="search" class="search-overlay-input" id="searchOverlayInput" name="q" placeholder="ابحث عن مشترك، كشاف، بريزة..." autocomplete="off" aria-label="بحث عن منتج" /><button type="submit" class="search-overlay-submit" aria-label="بحث"><i class="fas fa-search" aria-hidden="true"></i></button><button type="button" class="search-overlay-close" id="searchOverlayClose" aria-label="إغلاق البحث">✕</button></div><div class="search-suggestions"><p>الأكثر بحثاً</p><div class="search-suggestion-tags"><button type="button" class="search-tag">مشترك كهرباء</button><button type="button" class="search-tag">كشاف ليد</button><button type="button" class="search-tag">برايز</button><button type="button" class="search-tag">دواية</button><button type="button" class="search-tag">فيشة</button><button type="button" class="search-tag">لمبة ليد</button></div></div></form>`;
    document.body.appendChild(el);
    const closeOverlay = () => {
      el.classList.remove('open');
      el.setAttribute('aria-hidden', 'true');
    };
    document.getElementById('searchOverlayClose').addEventListener('click', closeOverlay);
    el.addEventListener('click', e => { if (e.target === el) closeOverlay(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && el.classList.contains('open')) closeOverlay(); });
    document.getElementById('searchOverlayForm').addEventListener('submit', e => {
      e.preventDefault();
      const input = document.getElementById('searchOverlayInput');
      const q = input?.value.trim();
      if (q) window.location.href = `/products/?q=${encodeURIComponent(q)}`;
    });
    el.querySelectorAll('.search-tag').forEach(tag => {
      tag.addEventListener('click', () => { window.location.href = `/products/?q=${encodeURIComponent(tag.textContent)}`; });
    });
  }
}

function openSearch() {
  const ov = document.getElementById('searchOverlay');
  if (ov) {
    ov.classList.add('open');
    ov.setAttribute('aria-hidden', 'false');
    setTimeout(() => document.getElementById('searchOverlayInput')?.focus(), 80);
  }
}

function initNewsletter() {
  const form = document.getElementById('newsletter-form');
  if (!form) return;
  form.addEventListener('submit', event => {
    event.preventDefault();
    const input = form.querySelector('input[type="email"]');
    if (!input?.checkValidity()) {
      input?.reportValidity();
      return;
    }
    UI.showToast('تم تسجيل بريدك لمتابعة أحدث العروض', '✉️');
    form.reset();
  });
}

// ============ Promo Banner ============
function initPromoBanner() {
  const btn = document.querySelector('.close-promo');
  const banner = document.querySelector('.promo-banner');
  if (!btn || !banner) return;
  btn.addEventListener('click', () => {
    banner.style.maxHeight = banner.scrollHeight + 'px';
    requestAnimationFrame(() => {
      banner.style.transition = 'max-height 0.3s ease, opacity 0.3s ease, padding 0.3s ease';
      banner.style.maxHeight = '0'; banner.style.opacity = '0'; banner.style.overflow = 'hidden'; banner.style.padding = '0';
    });
  });
}

// ============ Cart Buttons ============
function initCartButtons() {
  // Disabled: CartManager in cart.js handles all add-to-cart logic
}

// ============ Wishlist Buttons ============
function initWishlistButtons() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-action="wishlist"]');
    if (!btn) return;
    const id = btn.dataset.productId;
    if (!id) return;
    const card = btn.closest('[data-product-id]') || btn.closest('[data-product]');
    const data = card ? { id, name: card.dataset.productName || 'منتج', price: parseFloat(card.dataset.productPrice || 0), emoji: card.dataset.productEmoji || '📦', category: card.dataset.productCategory || 'منتجات', oldPrice: parseFloat(card.dataset.productOldPrice || 0), rating: parseFloat(card.dataset.productRating || 4.5), reviews: parseInt(card.dataset.productReviews || 0) } : null;
    const added = Store.toggleWishlist(id, data);
    btn.classList.toggle('active', added);
    btn.textContent = added ? '❤️' : '🤍';
    UI.showToast(added ? 'تمت الإضافة إلى المفضلة' : 'تمت الإزالة من المفضلة', added ? '❤️' : '🤍');
    if (typeof WishlistPage !== 'undefined') WishlistPage.render?.();
  });
}

// ============ Cart Page - Minimal (CartManager handles cart logic) ============
const CartPage = {
  init() {
    // CartManager in cart.js handles all cart functionality
    // This is just a placeholder for compatibility
  }
};

// ============ Wishlist Page ============
const WishlistPage = {
  currentFilter: 'all',
  init() { if (!document.querySelector('.wishlist-page')) return; this.render(); this.bindEvents(); },
  getFiltered() {
    const items = Store.wishlistItems;
    return this.currentFilter === 'all' ? items : items.filter(p => (p.category || 'عام') === this.currentFilter);
  },
  render() {
    const grid = document.getElementById('wishlistGrid');
    const empty = document.getElementById('wishlistEmpty');
    const total = Store.wishlistItems.length;
    document.querySelectorAll('.wishlist-total-count').forEach(el => el.textContent = total);
    const stickyText = document.getElementById('wlStickyText');
    if (stickyText) stickyText.innerHTML = `<strong>${total} منتج</strong> في مفضلتك`;
    if (!grid) return;
    if (total === 0) {
      grid.style.display = 'none'; empty?.classList.add('show');
      const sb = document.querySelector('.wishlist-sticky-bar'); if (sb) sb.style.display = 'none'; return;
    }
    empty?.classList.remove('show'); grid.style.display = 'grid';
    const sb = document.querySelector('.wishlist-sticky-bar'); if (sb) sb.style.display = '';
    const items = this.getFiltered();
    grid.innerHTML = items.map((item, i) => {
      const hasOld = item.oldPrice && item.oldPrice > item.price;
      const saving = hasOld ? Math.round(item.oldPrice - item.price) : 0;
      const savePct = hasOld ? Math.round((saving / item.oldPrice) * 100) : 0;
      return `<article class="wl-card" style="animation-delay:${i*0.06}s" data-product-id="${item.id}" data-product-name="${item.name}" data-product-price="${item.price}" data-product-emoji="${item.emoji||'📦'}" data-product-category="${item.category||'منتجات'}"><div class="wl-card-img"><span class="wl-card-emoji">${item.emoji||'📦'}</span><div class="wl-card-badges">${hasOld?`<span class="wl-badge wl-badge-sale">-${savePct}%</span>`:''}${item.isNew?`<span class="wl-badge wl-badge-new">جديد</span>`:''}</div><button class="wl-remove-btn" data-wl-remove="${item.id}" title="إزالة">✕</button>${hasOld?`<div class="wl-price-drop">وفّر ${saving} ج.م</div>`:''}</div><div class="wl-card-body"><div class="wl-card-cat">${item.category||'منتجات'}</div><div class="wl-card-name">${item.name}</div><div class="wl-card-rating"><span class="wl-stars">${'★'.repeat(Math.floor(item.rating||4))}</span><span class="wl-rating-num"> ${(item.rating||4).toFixed(1)} ${item.reviews?`(${item.reviews})`:''}</span></div><div class="wl-card-price-row"><div class="wl-price-wrap"><span class="wl-price-current">${UI.formatPrice(item.price)}</span>${hasOld?`<span class="wl-price-old">${UI.formatPrice(item.oldPrice)}</span>`:''}</div>${hasOld?`<span class="wl-price-save">وفّر ${savePct}%</span>`:''}</div><div class="wl-card-actions"><button class="wl-add-cart-btn" data-action="add-to-cart">🛒 أضف للسلة</button><button class="wl-share-btn" data-wl-share="${item.id}" title="مشاركة">🔗</button></div></div></article>`;
    }).join('');
  },
  bindEvents() {
    const grid = document.getElementById('wishlistGrid');
    if (grid) {
      grid.addEventListener('click', e => {
        const removeBtn = e.target.closest('[data-wl-remove]');
        if (removeBtn) {
          const card = removeBtn.closest('.wl-card');
          card.style.transition = '0.2s ease'; card.style.transform = 'scale(0.9)'; card.style.opacity = '0';
          setTimeout(() => { Store.removeFromWishlist(removeBtn.dataset.wlRemove); UI.showToast('تمت الإزالة من المفضلة','🤍'); this.render(); }, 200);
        }
        const shareBtn = e.target.closest('[data-wl-share]');
        if (shareBtn) this.openShareModal();
      });
    }
    document.querySelectorAll('.wcat-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.wcat-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentFilter = btn.dataset.cat || 'all';
        this.render();
      });
    });
    document.getElementById('addAllToCart')?.addEventListener('click', () => {
      const items = Store.wishlistItems; if (!items.length) return;
      items.forEach(item => Store.addToCart(item));
      UI.showToast(`تمت إضافة ${items.length} منتجات إلى السلة 🛒`);
    });
    document.getElementById('clearWishlist')?.addEventListener('click', () => {
      if (confirm('هل تريد مسح قائمة المفضلة كاملة؟')) { Store.wishlistIds=[]; Store.wishlistItems=[]; Store.saveWishlist(); this.render(); UI.showToast('تم مسح قائمة المفضلة','🗑️'); }
    });
    document.getElementById('wlShareClose')?.addEventListener('click', () => document.getElementById('wlShareModal')?.classList.remove('open'));
    document.getElementById('wlShareModalOverlay')?.addEventListener('click', () => document.getElementById('wlShareModal')?.classList.remove('open'));
    document.getElementById('wlCopyLink')?.addEventListener('click', () => { navigator.clipboard?.writeText(window.location.href).then(()=>UI.showToast('تم نسخ الرابط!','📋')); });
  },
  openShareModal() { const m = document.getElementById('wlShareModal'); const inp = document.getElementById('wlShareLinkInput'); if (m){if(inp) inp.value=window.location.href; m.classList.add('open');} }
};

// ============ Product Detail ============
const ProductDetail = {
  qty: 1,
  init() {
    if (!document.querySelector('.product-detail-page')) return;
    this.initGallery(); this.initImageZoom(); this.initTabs(); this.initVariants(); this.initQtySelector(); this.initAddToCart();
  },
  initGallery() {
    const thumbs = document.querySelectorAll('.gallery-thumb');
    const mainImg = document.querySelector('#main-product-image');

    thumbs.forEach(t => {
      t.addEventListener('click', () => {
        const newSrc = t.getAttribute('data-src');
        if (!newSrc || !mainImg) return;

        // تغيير الصورة
        mainImg.src = newSrc;

        // active class
        thumbs.forEach(x => {
          x.classList.remove('active');
          x.removeAttribute('aria-current');
        });
        t.classList.add('active');
        t.setAttribute('aria-current', 'true');
      });
    });
  },
  initImageZoom() {
    const galleryMain = document.querySelector('.gallery-main');
    const mainImg = document.querySelector('#main-product-image');
    if (!galleryMain || !mainImg) return;

    let zoomSurface = document.getElementById('productPressZoom');
    if (!zoomSurface) {
      zoomSurface = document.createElement('div');
      zoomSurface.id = 'productPressZoom';
      zoomSurface.className = 'product-press-zoom';
      zoomSurface.setAttribute('aria-hidden', 'true');
      zoomSurface.innerHTML = '<div class="product-press-zoom-label">حرّك الماوس لاستكشاف التفاصيل</div>';
      document.body.appendChild(zoomSurface);
    }

    const getPoint = (event) => {
      const rect = galleryMain.getBoundingClientRect();
      const x = Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100));
      const y = Math.max(0, Math.min(100, ((event.clientY - rect.top) / rect.height) * 100));
      return { x, y };
    };

    const updateZoomPosition = (event) => {
      if (!zoomSurface.classList.contains('open')) return;
      const point = getPoint(event);
      zoomSurface.style.setProperty('--zoom-x', `${point.x}%`);
      zoomSurface.style.setProperty('--zoom-y', `${point.y}%`);
    };

    const closeZoom = () => {
      zoomSurface.classList.remove('open');
      zoomSurface.setAttribute('aria-hidden', 'true');
      zoomSurface.style.backgroundImage = '';
      document.body.classList.remove('zoom-modal-open');
      window.removeEventListener('pointermove', updateZoomPosition);
      window.removeEventListener('pointerup', closeZoom);
      window.removeEventListener('pointercancel', closeZoom);
    };

    const openZoom = (event) => {
      if (event.button !== undefined && event.button !== 0) return;
      if (!mainImg.src) return;
      event.preventDefault();
      const src = mainImg.currentSrc || mainImg.src;
      zoomSurface.style.backgroundImage = `url("${src.replaceAll('"', '\\"')}")`;
      zoomSurface.classList.add('open');
      zoomSurface.setAttribute('aria-hidden', 'false');
      document.body.classList.add('zoom-modal-open');
      updateZoomPosition(event);
      window.addEventListener('pointermove', updateZoomPosition);
      window.addEventListener('pointerup', closeZoom);
      window.addEventListener('pointercancel', closeZoom);
    };

    galleryMain.setAttribute('tabindex', '0');
    galleryMain.setAttribute('aria-label', 'اضغط باستمرار على صورة المنتج للتكبير');
    galleryMain.addEventListener('pointerdown', openZoom);
    galleryMain.addEventListener('dragstart', (event) => event.preventDefault());
  },
  initTabs() {
    const tabs = Array.from(document.querySelectorAll('.tab-btn'));
    const contents = document.querySelectorAll('.tab-content');
    if (!tabs.length) return;

    const activate = (tab, shouldFocus = false) => {
      tabs.forEach(t => {
        const selected = t === tab;
        t.classList.toggle('active', selected);
        t.setAttribute('aria-selected', selected ? 'true' : 'false');
        t.setAttribute('tabindex', selected ? '0' : '-1');
      });
      contents.forEach(content => {
        const selected = content.id === tab.dataset.tab;
        content.classList.toggle('active', selected);
        content.hidden = !selected;
      });
      if (shouldFocus) tab.focus();
    };

    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => activate(tab));
      tab.addEventListener('keydown', event => {
        const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];
        if (!keys.includes(event.key)) return;
        event.preventDefault();
        let nextIndex = index;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = tabs.length - 1;
        if (event.key === 'ArrowLeft') nextIndex = (index + 1) % tabs.length;
        if (event.key === 'ArrowRight') nextIndex = (index - 1 + tabs.length) % tabs.length;
        activate(tabs[nextIndex], true);
      });
    });

    activate(tabs.find(tab => tab.classList.contains('active')) || tabs[0]);
  },
  initVariants() {
    document.querySelectorAll('.color-option,.size-option').forEach(o=>o.addEventListener('click',()=>{if(o.classList.contains('disabled'))return;const g=o.closest('.color-options,.size-options');g?.querySelectorAll('.color-option,.size-option').forEach(x=>x.classList.remove('active'));o.classList.add('active');}));
  },
  initQtySelector() {
    const m=document.getElementById('qty-minus');const p=document.getElementById('qty-plus');const d=document.getElementById('qty-display');
    m?.addEventListener('click',()=>{this.qty=Math.max(1,this.qty-1);if(d)d.textContent=this.qty;});
    p?.addEventListener('click',()=>{this.qty=Math.min(10,this.qty+1);if(d)d.textContent=this.qty;});
  },
  initAddToCart() {
    // Disabled: CartManager in cart.js handles this via bindAddToCartButtons
  }
};

// ============ Hero Slider ============
const HeroSlider = {
  current: 0,
  total: 0,
  interval: null,
  delay: 4000,
  init() {
    const slider = document.getElementById('heroSlider');
    if (!slider) return;
    const slides = slider.querySelectorAll('.slide');
    this.total = slides.length;
    if (this.total === 0) return;
    
    const activeIndex = Array.from(slides).findIndex(s => s.classList.contains('active'));
    this.current = activeIndex >= 0 ? activeIndex : 0;
    this.loadSlideImage(slides[this.current]);
    
    if (!slider.querySelector('.slider-dots')) {
      const dotsWrap = document.createElement('div');
      dotsWrap.className = 'slider-dots';
      dotsWrap.setAttribute('role', 'tablist');
      dotsWrap.setAttribute('aria-label', 'التنقل بين الشرائح');
      for (let i = 0; i < this.total; i++) {
        const b = document.createElement('button');
        b.className = 'dot' + (i === this.current ? ' active' : '');
        b.type = 'button';
        b.setAttribute('aria-label', `الشريحة ${i + 1}`);
        if (i === this.current) b.setAttribute('aria-current', 'true');
        dotsWrap.appendChild(b);
      }
      slider.appendChild(dotsWrap);
    }

    const dotsWrap = slider.querySelector('.slider-dots');
    if (dotsWrap) {
      dotsWrap.setAttribute('role', 'tablist');
      dotsWrap.setAttribute('aria-label', 'التنقل بين الشرائح');
    }
    const dots = slider.querySelectorAll('.dot');
    dots.forEach((dot, i) => {
      dot.type = 'button';
      dot.setAttribute('aria-label', `الشريحة ${i + 1}`);
      if (i === this.current) {
        dot.setAttribute('aria-current', 'true');
      } else {
        dot.removeAttribute('aria-current');
      }
    });
    slider.querySelector('.slider-prev')?.addEventListener('click', () => { this.prev(); this.resetAuto(); });
    slider.querySelector('.slider-next')?.addEventListener('click', () => { this.next(); this.resetAuto(); });
    dots.forEach((dot, i) => dot.addEventListener('click', () => { this.goTo(i); this.resetAuto(); }));

    runWhenIdle(() => this.loadDeferredSlides(), 2500);
    this.startAuto();
    slider.addEventListener('mouseenter', () => this.stopAuto());
    slider.addEventListener('mouseleave', () => this.startAuto());
    slider.addEventListener('focusin', () => this.stopAuto());
    slider.addEventListener('focusout', () => this.startAuto());
  },
  goTo(n) {
    const slider = document.getElementById('heroSlider');
    if (!slider) return;
    const slides = slider.querySelectorAll('.slide');
    const dots = slider.querySelectorAll('.dot');
    const nextIndex = (n + this.total) % this.total;
    this.loadSlideImage(slides[nextIndex]);
    slides[this.current]?.classList.remove('active');
    if (dots[this.current]) { dots[this.current].classList.remove('active'); dots[this.current].removeAttribute('aria-current'); }
    this.current = nextIndex;
    slides[this.current]?.classList.add('active');
    if (dots[this.current]) { dots[this.current].classList.add('active'); dots[this.current].setAttribute('aria-current','true'); }
  },
  loadSlideImage(slide) {
    if (!slide || slide.dataset.loaded === 'true') return;
    slide.querySelectorAll('source[data-srcset]').forEach(source => {
      source.srcset = source.dataset.srcset;
      source.removeAttribute('data-srcset');
    });
    const image = slide.querySelector('img[data-src]');
    if (image) {
      image.src = image.dataset.src;
      image.removeAttribute('data-src');
    }
    slide.dataset.loaded = 'true';
  },
  loadDeferredSlides() {
    const slider = document.getElementById('heroSlider');
    if (!slider) return;
    slider.querySelectorAll('.slide').forEach((slide, index) => {
      if (index !== this.current) this.loadSlideImage(slide);
    });
  },
  next() { this.goTo(this.current + 1); },
  prev() { this.goTo(this.current - 1); },
  startAuto() {
    this.stopAuto();
    if (this.total <= 1) return;
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
    this.interval = setInterval(() => this.next(), this.delay);
  },
  stopAuto() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  },
  resetAuto() { this.stopAuto(); this.startAuto(); }
};

// ============ Home Product Tabs ============
const HomeProductTabs = {
  init() {
    const root = document.querySelector('[data-home-product-tabs]');
    if (!root) return;

    const buttons = root.querySelectorAll('[data-product-tab]');
    const grid = root.querySelector('[data-products-grid]');
    const status = root.querySelector('[data-products-status]');
    const empty = root.querySelector('[data-products-empty]');
    const heading = root.querySelector('[data-home-products-heading]');
    const description = root.querySelector('[data-home-products-description]');
    const tabList = root.querySelector('.product-tabs');
    const apiUrl = root.dataset.apiUrl;
    const limit = root.dataset.limit || '10';
    if (!buttons.length || !grid || !apiUrl) return;

    this.ensureInitialTab(root, buttons, { grid, heading, description });

    buttons.forEach((button, index) => {
      button.addEventListener('click', () => {
        if (button.classList.contains('active')) return;
        this.activate(root, button, { grid, status, empty, heading, description, apiUrl, limit });
      });
      button.addEventListener('keydown', event => {
        const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];
        if (!keys.includes(event.key)) return;
        event.preventDefault();
        let nextIndex = index;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = buttons.length - 1;
        if (event.key === 'ArrowLeft') nextIndex = (index + 1) % buttons.length;
        if (event.key === 'ArrowRight') nextIndex = (index - 1 + buttons.length) % buttons.length;
        const nextButton = buttons[nextIndex];
        nextButton.focus();
        if (!nextButton.classList.contains('active')) {
          this.activate(root, nextButton, { grid, status, empty, heading, description, apiUrl, limit });
        }
      });
    });
  },

  async activate(root, activeButton, refs) {
    const { grid, status, empty, heading, description, apiUrl, limit } = refs;
    const type = activeButton.dataset.productTab;
    const requestId = (this.requestId || 0) + 1;
    this.requestId = requestId;

    root.querySelectorAll('[data-product-tab]').forEach(button => {
      const isActive = button === activeButton;
      button.classList.toggle('active', isActive);
      button.setAttribute('aria-selected', isActive ? 'true' : 'false');
      button.setAttribute('tabindex', isActive ? '0' : '-1');
    });
    if (grid && activeButton.id) grid.setAttribute('aria-labelledby', activeButton.id);
    root.dataset.activeProductTab = type;

    root.classList.add('is-switching');
    if (heading) heading.textContent = activeButton.dataset.heading || activeButton.textContent.trim();
    if (description) description.textContent = activeButton.dataset.description || '';
    this.setStatus(status, 'جاري تحميل المنتجات...');
    if (empty) empty.hidden = true;
    grid.classList.add('is-loading');

    try {
      const url = new URL(apiUrl, window.location.origin);
      url.searchParams.set('type', type);
      url.searchParams.set('limit', limit);

      const response = await fetch(url, {
        cache: 'no-store',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.message || 'تعذر تحميل المنتجات');
      if (requestId !== this.requestId) return;

      grid.innerHTML = data.products.map(product => this.renderProduct(product)).join('');
      if (empty) empty.hidden = data.products.length > 0;
      this.clearStatus(status);
    } catch (error) {
      if (requestId !== this.requestId) return;
      this.setStatus(status, error.message || 'حدث خطأ أثناء تحميل المنتجات. حاول مرة أخرى.');
    } finally {
      if (requestId !== this.requestId) return;
      grid.classList.remove('is-loading');
      root.classList.remove('is-switching');
    }
  },

  ensureInitialTab(root, buttons, refs) {
    const initialButton = Array.from(buttons).find(button => button.dataset.productTab === 'offers') || buttons[0];
    if (!initialButton) return;

    buttons.forEach(button => {
      const isActive = button === initialButton;
      button.classList.toggle('active', isActive);
      button.setAttribute('aria-selected', isActive ? 'true' : 'false');
      button.setAttribute('tabindex', isActive ? '0' : '-1');
    });

    if (refs.grid && initialButton.id) refs.grid.setAttribute('aria-labelledby', initialButton.id);
    if (refs.heading) refs.heading.textContent = initialButton.dataset.heading || initialButton.textContent.trim();
    if (refs.description) refs.description.textContent = initialButton.dataset.description || '';
    root.dataset.activeProductTab = initialButton.dataset.productTab || 'offers';
  },

  renderProduct(product) {
    const image = product.image
      ? `<img src="${this.escape(product.image)}" alt="${this.escape(product.image_alt || product.name)}" width="400" height="400" loading="lazy" decoding="async">`
      : '<div class="product-img-placeholder"><i class="fas fa-image"></i></div>';
    const discountLabel = product.discount_percent ? `خصم ${this.escape(product.discount_percent)}%` : 'خصم';
    const rating = Number(product.rating || 5).toFixed(1);
    const badges = [
      product.has_offer ? `<span class="badge-sale">${discountLabel}</span>` : '',
      product.is_hot ? '<span class="badge-hot">رائج</span>' : '',
      product.is_new ? '<span class="badge-new">جديد</span>' : ''
    ].join('');
    const oldPrice = product.old_price
      ? `<span class="price-original">${this.escape(product.old_price)} ج.م</span>`
      : '';
    const action = product.is_simple
      ? `<button class="add-to-cart-btn" data-action="add-to-cart" data-product-id="${product.id}" data-product-name="${this.escape(product.name)}" data-product-price="${this.escape(product.price)}" data-quantity="1" data-product-image="${this.escape(product.image || '')}" aria-label="أضف ${this.escape(product.name)} إلى السلة">
          <i class="fas fa-shopping-cart"></i>
        </button>`
      : `<a class="add-to-cart-btn choose-options-btn" href="${this.escape(product.url)}" aria-label="اختيار مواصفات ${this.escape(product.name)}">
          <i class="fas fa-sliders"></i>
        </a>`;

    return `
      <article class="product-card home-product-card">
        <div class="product-image-wrap">
          <a href="${this.escape(product.url)}">${image}</a>
          <div class="product-badges">${badges}</div>
          <a href="${this.escape(product.url)}" class="product-image-cta">عرض التفاصيل</a>
        </div>
        <div class="product-info">
          <div class="product-meta-row">
            <div class="product-category-tag">${this.escape(product.category || '')}</div>
            <div class="product-rating-mini" aria-label="تقييم ${rating} من 5">
              <i class="fas fa-star" aria-hidden="true"></i>
              <span>${rating}</span>
            </div>
          </div>
          <h3 class="product-name"><a href="${this.escape(product.url)}">${this.escape(product.name)}</a></h3>
          <div class="product-price-row">
            <div class="price-group">
              <span class="price-current">${this.escape(product.price)} ج.م</span>
              ${oldPrice}
            </div>
            ${action}
          </div>
        </div>
      </article>
    `;
  },

  setStatus(status, message) {
    if (!status) return;
    status.textContent = message;
    status.hidden = false;
  },

  clearStatus(status) {
    if (!status) return;
    status.textContent = '';
    status.hidden = true;
  },

  escape(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }
};

// ============ Filter Toggle ============
function initFilterToggle() {
  const btn=document.querySelector('.filter-toggle-btn'); const sidebar=document.querySelector('.filter-sidebar');
  if(!btn||!sidebar)return;
  btn.addEventListener('click',()=>{const o=sidebar.classList.toggle('open');btn.innerHTML=o?'✕ إغلاق الفلتر':'⚙️ الفلاتر';});
}

// ============ Active Nav ============
function setActiveNavLinks() {
  const currentPath = location.pathname.replace(/\/+$/, '') || '/';
  document.querySelectorAll('.navbar-links a, .mobile-menu-links a, .bottom-nav a').forEach(a => {
    const href = a.getAttribute('href');
    if (!href || href === '#') return;
    const linkPath = new URL(href, location.origin).pathname.replace(/\/+$/, '') || '/';
    a.classList.remove('active');
    if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath + '/'))) {
      a.classList.add('active');
    }
  });
}

// ============ Sync wishlist button states ============
function syncWishlistBtns() {
  document.querySelectorAll('[data-action="wishlist"]').forEach(btn => {
    const id = btn.dataset.productId;
    if (id) { const w = Store.isWishlisted(id); btn.classList.toggle('active', w); btn.textContent = w ? '❤️' : '🤍'; }
  });
}

// ============ Bootstrap ============
function initPage() {
  const isHomePage = Boolean(document.querySelector('.home-page'));

  MobileMenu.init(); initSearch(); initCartButtons();
  setActiveNavLinks(); UI.updateCartBadge();
  HeroSlider.init(); HomeProductTabs.init();

  const initNonCriticalFeatures = () => {
    initPromoBanner(); initNewsletter(); initWishlistButtons();
    syncWishlistBtns(); UI.updateWishlistBadge();
    ProductDetail.init(); WishlistPage.init(); initFilterToggle();
  };

  // CartPage.init(); // Disabled - CartManager handles cart 
  if (isHomePage) {
    runWhenIdle(initNonCriticalFeatures, 2500);
  } else {
    initNonCriticalFeatures();
  }
}

document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', initPage) : initPage();

// ============ Auth State in Navbar ============
function initAuthNav() {
  const user = JSON.parse(localStorage.getItem('noor_user') || 'null');
  const accountBtns = document.querySelectorAll('.nav-icon-btn[aria-label="حسابي"]');
  accountBtns.forEach(btn => {
    if (user) {
      btn.href = 'profile.html';
      btn.textContent = user.avatar || '👤';
      btn.title = user.name || 'حسابي';
    } else {
      btn.href = 'login.html';
    }
  });
}

// Run auth nav init after page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAuthNav);
} else {
  initAuthNav();
}
