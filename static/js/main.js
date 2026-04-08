/* ============================================
   متجر نور - Main JavaScript
   Vanilla JS - No Dependencies
   ============================================ */

'use strict';

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
    el.innerHTML = `<div class="search-overlay-box"><div class="search-overlay-input-wrap"><span style="font-size:1.2rem">🔍</span><input type="search" class="search-overlay-input" id="searchOverlayInput" placeholder="ابحث عن منتج، ماركة..." autocomplete="off" /><button class="search-overlay-close" id="searchOverlayClose">✕</button></div><div class="search-suggestions"><p>🔥 الأكثر بحثاً</p><div class="search-suggestion-tags"><span class="search-tag">سماعات</span><span class="search-tag">ساعات ذكية</span><span class="search-tag">أحذية</span><span class="search-tag">عطور</span><span class="search-tag">حقائب</span><span class="search-tag">كاميرات</span></div></div></div>`;
    document.body.appendChild(el);
    const closeOverlay = () => el.classList.remove('open');
    document.getElementById('searchOverlayClose').addEventListener('click', closeOverlay);
    el.addEventListener('click', e => { if (e.target === el) closeOverlay(); });
    document.getElementById('searchOverlayInput').addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.target.value.trim()) window.location.href = `products.html?q=${encodeURIComponent(e.target.value.trim())}`;
    });
    el.querySelectorAll('.search-tag').forEach(tag => {
      tag.addEventListener('click', () => { window.location.href = `products.html?q=${encodeURIComponent(tag.textContent)}`; });
    });
  }
  // open on search btn click
  document.querySelectorAll('.search-btn').forEach(btn => {
    btn.addEventListener('click', openSearch);
  });
  // mobile row2 input opens overlay
  const mobileInput = document.querySelector('.navbar-row2 .search-box input');
  if (mobileInput) {
    mobileInput.addEventListener('mousedown', e => { e.preventDefault(); openSearch(); });
    mobileInput.addEventListener('focus', e => { e.target.blur(); openSearch(); });
  }
  // desktop search input
  const desktopInput = document.querySelector('.navbar-row2-desktop .search-box input, .navbar-search .search-box input');
  if (desktopInput && !desktopInput.closest('.navbar-row2')) {
    desktopInput.addEventListener('focus', openSearch);
  }
}

function openSearch() {
  const ov = document.getElementById('searchOverlay');
  if (ov) { ov.classList.add('open'); setTimeout(() => document.getElementById('searchOverlayInput')?.focus(), 80); }
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
    this.initGallery(); this.initTabs(); this.initVariants(); this.initQtySelector(); this.initAddToCart();
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
        thumbs.forEach(x => x.classList.remove('active'));
        t.classList.add('active');
      });
    });
  },
  initTabs() {
    const tabs=document.querySelectorAll('.tab-btn'); const contents=document.querySelectorAll('.tab-content');
    tabs.forEach(tab=>tab.addEventListener('click',()=>{tabs.forEach(t=>t.classList.remove('active'));contents.forEach(c=>c.classList.remove('active'));tab.classList.add('active');const target=document.getElementById(tab.dataset.tab);if(target)target.classList.add('active');}));
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
  init() {
    const slider = document.getElementById('heroSlider');
    if (!slider) return;
    const slides = slider.querySelectorAll('.slide');
    this.total = slides.length;
    if (this.total === 0) return;
    
    const activeIndex = Array.from(slides).findIndex(s => s.classList.contains('active'));
    this.current = activeIndex >= 0 ? activeIndex : 0;
    
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

    const dots = slider.querySelectorAll('.dot');
    slider.querySelector('.slider-prev')?.addEventListener('click', () => { this.prev(); this.resetAuto(); });
    slider.querySelector('.slider-next')?.addEventListener('click', () => { this.next(); this.resetAuto(); });
    dots.forEach((dot, i) => dot.addEventListener('click', () => { this.goTo(i); this.resetAuto(); }));

    this.startAuto();
    slider.addEventListener('mouseenter', () => this.stopAuto());
    slider.addEventListener('mouseleave', () => this.startAuto());
  },
  goTo(n) {
    const slider = document.getElementById('heroSlider');
    if (!slider) return;
    const slides = slider.querySelectorAll('.slide');
    const dots = slider.querySelectorAll('.dot');
    slides[this.current]?.classList.remove('active');
    if (dots[this.current]) { dots[this.current].classList.remove('active'); dots[this.current].removeAttribute('aria-current'); }
    this.current = (n + this.total) % this.total;
    slides[this.current]?.classList.add('active');
    if (dots[this.current]) { dots[this.current].classList.add('active'); dots[this.current].setAttribute('aria-current','true'); }
  },
  next() { this.goTo(this.current + 1); },
  prev() { this.goTo(this.current - 1); },
  startAuto() { this.interval = setInterval(() => this.next(), 3000); },
  stopAuto() { clearInterval(this.interval); },
  resetAuto() { this.stopAuto(); this.startAuto(); }
};

// ============ Filter Toggle ============
function initFilterToggle() {
  const btn=document.querySelector('.filter-toggle-btn'); const sidebar=document.querySelector('.filter-sidebar');
  if(!btn||!sidebar)return;
  btn.addEventListener('click',()=>{const o=sidebar.classList.toggle('open');btn.innerHTML=o?'✕ إغلاق الفلتر':'⚙️ الفلاتر';});
}

// ============ Active Nav ============
function setActiveNavLinks() {
  const current = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.navbar-links a, .mobile-menu-links a, .bottom-nav a').forEach(a => {
    const href = a.getAttribute('href');
    a.classList.remove('active');
    if (href === current || (current === '' && href === 'index.html')) a.classList.add('active');
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
  MobileMenu.init(); initSearch(); initPromoBanner(); initCartButtons(); initWishlistButtons();
  setActiveNavLinks(); syncWishlistBtns(); UI.updateCartBadge(); UI.updateWishlistBadge();
  // CartPage.init(); // Disabled - CartManager handles cart 
  ProductDetail.init(); WishlistPage.init(); initFilterToggle(); HeroSlider.init();
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
