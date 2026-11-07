///** @odoo-module **/
//import publicWidget from "@web/legacy/js/public/public_widget";
//
//publicWidget.registry.PXMProductOptionalAlternative = publicWidget.Widget.extend({
//    selector: ".pxm-product-actions",
//
//    start() {
//        this._attachOptionalHandler();
//        this._attachAlternativeHandler();
//        return this._super(...arguments);
//    },
//
//    // ========================================
//    // OPTIONAL PRODUCTS HANDLER
//    // ========================================
//    _attachOptionalHandler() {
//        const optionalBtn = this.el.querySelector('.pxm-optional-btn');
//        if (!optionalBtn) return;
//
//        optionalBtn.addEventListener('click', async (ev) => {
//            ev.preventDefault();
//            await this._showOptionalModal();
//            console.log("KKKKKKKKKKKKKKKKKKKKKKKKKKKK")
//        });
//    },
//
//    async _showOptionalModal() {
//        const currentProductId =
//            document.getElementById('pxm-product-root')?.dataset.productId;
//
//        if (!currentProductId) {
//            this._showNotification('Product ID not found', 'warning');
//            return;
//        }
//
//        const products = await this._fetchOptionalProducts(currentProductId);
//
//        if (!products || products.length === 0) {
//            this._showNotification('No optional products available', 'info');
//            return;
//        }
//
//        const overlay = document.createElement('div');
//        overlay.id = 'pxm-optional-overlay';
//        overlay.className = 'pxm-overlay pxm-optional-overlay';
//
//        const modal = document.createElement('div');
//        modal.className = 'pxm-optional-modal';
//        modal.innerHTML = this._generateOptionalModalHTML(products);
//
//        overlay.appendChild(modal);
//        document.body.appendChild(overlay);
//
//        this._attachOptionalModalEvents(overlay, products);
//    },
//
//    async _fetchOptionalProducts(productId) {
//        try {
//            const response = await fetch('/pxm/shop/optional_products', {
//                method: 'POST',
//                headers: { 'Content-Type': 'application/json' },
//                body: JSON.stringify({
//                    jsonrpc: "2.0",
//                    method: "call",
//                    params: { product_id: parseInt(productId) }
//                })
//            });
//
//            if (!response.ok) throw new Error('Failed to fetch optional products');
//
//            const result = await response.json();
//            const products = result.result?.products || [];
//
//            return products.map(p => ({
//                id: p.id,
//                name: p.name || 'Product',
//                price: p.price_html || '$0.00',
//                list_price: p.list_price || 0,
//                image: p.image_1920
//                    ? `data:image/png;base64,${p.image_1920}`
//                    : `/web/image/product.template/${p.id}/image_1920`,
//                url: `/pxm/product/${p.id}`,
//                description: p.description_sale || '',
//                in_stock: p.qty_available > 0
//            }));
//        } catch (err) {
//            console.error("Failed to load optional products:", err);
//            return [];
//        }
//    },
//
//    _generateOptionalModalHTML(products) {
//        return `
//            <div class="optional-header">
//                <div class="optional-header-content">
//                    <div class="optional-icon-wrapper">
//                        <i class="fa fa-plus-circle"></i>
//                    </div>
//                    <div class="optional-title-section">
//                        <h2 class="optional-title">Optional Add-On Products</h2>
//                        <p class="optional-subtitle">Enhance your purchase with these complementary products</p>
//                    </div>
//                </div>
//                <button class="pxm-close-btn"
//                        type="button"
//                        aria-label="Close"
//                        onclick="this.closest('.pxm-overlay').remove()">
//                    <svg viewBox="0 0 24 24" class="pxm-close-icon">
//                        <line x1="18" y1="6" x2="6" y2="18"></line>
//                        <line x1="6" y1="6" x2="18" y2="18"></line>
//                    </svg>
//                </button>
//
//            </div>
//            <div class="optional-body">
//                <div class="optional-search-bar">
//                    <div class="search-input-wrapper">
//                        <i class="fa fa-search search-icon"></i>
//                        <input
//                            type="text"
//                            id="optional-search-input"
//                            class="optional-search-input"
//                            placeholder="Search optional products..."
//                            autocomplete="off"
//                        />
//                        <span class="search-results-count" id="optional-search-count"></span>
//                    </div>
//                </div>
//                <div class="optional-products-grid" id="optional-products-grid">
//                    ${products.map(p => `
//                        <div class="optional-product-card" data-product-id="${p.id}" data-product-name="${p.name.toLowerCase()}">
//                            <div class="optional-product-image-wrapper">
//                                <img src="${p.image}" alt="${p.name}" class="optional-product-image" loading="lazy" onerror="this.src='/images/Product.jpg'">
//
//                            </div>
//                            <div class="optional-product-content">
//                                <h3 class="optional-product-name" title="${p.name}">${p.name}</h3>
//                                ${p.description ? `<p class="optional-product-description">${p.description.substring(0, 100)}${p.description.length > 100 ? '...' : ''}</p>` : ''}
//                                <div class="optional-product-footer">
//                                    <div class="optional-product-price">${p.price}</div>
//                                    <div class="optional-product-actions">
//                                        <button class="optional-view-btn" onclick="window.location.href='${p.url}'">
//                                            <i class="fa fa-eye"></i>
//                                            View
//                                        </button>
//                                    </div>
//                                </div>
//                            </div>
//                        </div>
//                    `).join('')}
//                </div>
//                <div class="no-results-message" id="optional-no-results" style="display:none;">
//                    <i class="fa fa-search"></i>
//                    <p>No optional products found</p>
//                </div>
//            </div>
//            <div class="optional-footer">
//                <div class="optional-footer-info">
//                    <i class="fa fa-info-circle"></i>
//                    <span>Select products to add to your cart</span>
//                </div>
//            </div>
//        `;
//    },
//
//    _attachOptionalModalEvents(overlay, products) {
//        const searchInput = overlay.querySelector('#optional-search-input');
//        const searchCount = overlay.querySelector('#optional-search-count');
//        const grid = overlay.querySelector('#optional-products-grid');
//        const noResults = overlay.querySelector('#optional-no-results');
//        const cards = overlay.querySelectorAll('.optional-product-card');
//
//        // Search functionality
//        searchInput.addEventListener('input', (e) => {
//            const query = e.target.value.toLowerCase().trim();
//            let visibleCount = 0;
//
//            cards.forEach(card => {
//                const productName = card.dataset.productName;
//                if (!query || productName.includes(query)) {
//                    card.style.display = '';
//                    visibleCount++;
//                } else {
//                    card.style.display = 'none';
//                }
//            });
//
//            if (query) {
//                searchCount.textContent = `${visibleCount} result${visibleCount !== 1 ? 's' : ''}`;
//                searchCount.style.display = 'inline-block';
//            } else {
//                searchCount.style.display = 'none';
//            }
//
//            if (visibleCount === 0) {
//                grid.style.display = 'none';
//                noResults.style.display = 'flex';
//            } else {
//                grid.style.display = 'grid';
//                noResults.style.display = 'none';
//            }
//        });
//
//        // Add to cart buttons
//        const addButtons = overlay.querySelectorAll('.optional-add-btn');
//        addButtons.forEach(btn => {
//            btn.addEventListener('click', async (e) => {
//                e.stopPropagation();
//                const productId = btn.dataset.productId;
//                await this._addToCart(productId, btn);
//            });
//        });
//
//        // Close handlers
//        overlay.addEventListener('click', (e) => {
//            if (e.target === overlay) overlay.remove();
//        });
//
//        document.addEventListener('keydown', (e) => {
//            if (e.key === 'Escape') overlay.remove();
//        });
//    },
//
//    // ========================================
//    // ALTERNATIVE PRODUCTS HANDLER
//    // ========================================
//    _attachAlternativeHandler() {
//        const alternativeBtn = this.el.querySelector('.pxm-alternative-btn');
//        if (!alternativeBtn) return;
//
//        alternativeBtn.addEventListener('click', async (ev) => {
//            ev.preventDefault();
//            const currentProductId = alternativeBtn.dataset.currentProductId;
//            await this._showAlternativeModal(currentProductId);
//        });
//    },
//
//    async _showAlternativeModal(currentProductId) {
//        if (!currentProductId) {
//            this._showNotification('Product ID not found', 'warning');
//            return;
//        }
//        const products = await this._fetchAlternativeProducts(currentProductId);
//        console.log('Alternative products response:', products);
//
//        if (!products || products.length === 0) {
//            this._showNotification('No alternative products available', 'info');
//            return;
//        }
//        const overlay = document.createElement('div');
//        overlay.id = 'pxm-alternative-overlay';
//        overlay.className = 'pxm-overlay pxm-alternative-overlay';
//
//        const modal = document.createElement('div');
//        modal.className = 'pxm-alternative-modal';
//        modal.innerHTML = this._generateAlternativeModalHTML(products, currentProductId);
//
//        overlay.appendChild(modal);
//        document.body.appendChild(overlay);
//
//        this._attachAlternativeModalEvents(overlay, products);
//    },
//
//    async _fetchAlternativeProducts(productId) {
//        try {
//            const response = await fetch('/pxm/shop/alternative_products', {
//                method: 'POST',
//                headers: { 'Content-Type': 'application/json' },
//                body: JSON.stringify({
//                    jsonrpc: "2.0",
//                    method: "call",
//                    params: { product_id: parseInt(productId) }
//                })
//            });
//
//            if (!response.ok) throw new Error('Failed to fetch alternative products');
//
//            const result = await response.json();
//            const products = result.result?.products || [];
//
//            return products.map(p => ({
//                id: p.id,
//                name: p.name || 'Product',
//                price: p.price_html || '$0.00',
//                list_price: p.list_price || 0,
//                image: p.image_1920
//                    ? `data:image/png;base64,${p.image_1920}`
//                    : `/web/image/product.template/${p.id}/image_1920`,
//                url: `/pxm/product/${p.id}`,
//                description: p.description_sale || '',
//                specs: p.dynamic_values || {},
//                in_stock: p.qty_available > 0,
//                rating: p.rating || 0
//            }));
//        } catch (err) {
//            console.error("Failed to load alternative products:", err);
//            return [];
//        }
//    },
//
//    _generateAlternativeModalHTML(products, currentProductId) {
//        return `
//            <div class="alternative-header">
//                <div class="alternative-header-content">
//                    <div class="alternative-icon-wrapper">
//                        <i class="fa fa-exchange-alt"></i>
//                    </div>
//                    <div class="alternative-title-section">
//                        <h2 class="alternative-title">Alternative Products</h2>
//                        <p class="alternative-subtitle">Explore similar options that might better suit your needs</p>
//                    </div>
//                </div>
//                <button class="pxm-close-btn" style="display: block;" onclick="this.closest('.pxm-overlay').remove()">
//                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
//                        <line x1="18" y1="6" x2="6" y2="18"></line>
//                        <line x1="6" y1="6" x2="18" y2="18"></line>
//                    </svg>
//                </button>
//            </div>
//            <div class="alternative-body">
//                <div class="alternative-filters">
//                    <div class="filter-group">
//                        <label class="filter-label">
//                            <i class="fa fa-filter"></i>
//                            Filter by:
//                        </label>
//                        <div class="filter-buttons">
//                            <button class="filter-btn active" data-filter="all">
//                                All Products
//                            </button>
//                            <button class="filter-btn" data-filter="in-stock">
//                                <i class="fa fa-check-circle"></i>
//                                In Stock
//                            </button>
//                            <button class="filter-btn" data-filter="price-low">
//                                <i class="fa fa-arrow-down"></i>
//                                Price: Low to High
//                            </button>
//                            <button class="filter-btn" data-filter="price-high">
//                                <i class="fa fa-arrow-up"></i>
//                                Price: High to Low
//                            </button>
//                        </div>
//                    </div>
//                    <div class="alternative-search-bar">
//                        <div class="search-input-wrapper">
//                            <i class="fa fa-search search-icon"></i>
//                            <input
//                                type="text"
//                                id="alternative-search-input"
//                                class="alternative-search-input"
//                                placeholder="Search alternative products..."
//                                autocomplete="off"
//                            />
//                            <span class="search-results-count" id="alternative-search-count"></span>
//                        </div>
//                    </div>
//                </div>
//                <div class="alternative-products-grid" id="alternative-products-grid">
//                    ${products.map(p => `
//                        <div class="alternative-product-card"
//                             data-product-id="${p.id}"
//                             data-product-name="${p.name.toLowerCase()}"
//                             data-price="${p.list_price}"
//                             data-in-stock="${p.in_stock}">
//                            <div class="alternative-product-badges">
//                                ${!p.in_stock ? '<span class="badge badge-out-of-stock">Out of Stock</span>' : '<span class="badge badge-in-stock">In Stock</span>'}
//                            </div>
//                            <div class="alternative-product-image-wrapper">
//                                <img src="${p.image}" alt="${p.name}" class="alternative-product-image" loading="lazy" onerror="this.src='/images/Product.jpg'">
//                            </div>
//                            <div class="alternative-product-content">
//                                <h3 class="alternative-product-name" title="${p.name}">${p.name}</h3>
//                                ${p.rating > 0 ? `
//                                    <div class="alternative-product-rating">
//                                        ${'<i class="fa fa-star"></i>'.repeat(Math.floor(p.rating))}
//                                        ${p.rating % 1 !== 0 ? '<i class="fa fa-star-half-alt"></i>' : ''}
//                                        <span class="rating-value">${p.rating.toFixed(1)}</span>
//                                    </div>
//                                ` : ''}
//                                ${p.description ? `<p class="alternative-product-description">${p.description.substring(0, 120)}${p.description.length > 120 ? '...' : ''}</p>` : ''}
//                                ${Object.keys(p.specs).length > 0 ? `
//                                    <div class="alternative-product-specs">
//                                        ${Object.entries(p.specs).slice(0, 3).map(([key, value]) => `
//                                            <div class="spec-item">
//                                                <span class="spec-label">${key}:</span>
//                                                <span class="spec-value">${value}</span>
//                                            </div>
//                                        `).join('')}
//                                    </div>
//                                ` : ''}
//                                <div class="alternative-product-footer">
//                                    <div class="alternative-product-price">${p.price}</div>
//                                    <div class="alternative-product-actions">
//                                        <button class="alternative-view-btn" onclick="window.location.href='${p.url}'">
//                                            <i class="fa fa-eye"></i>
//                                            View Details
//                                        </button>
//                                        <button class="alternative-compare-btn" data-product-id="${p.id}">
//                                            <i class="fa fa-balance-scale"></i>
//                                            Compare
//                                        </button>
//                                    </div>
//                                </div>
//                            </div>
//                        </div>
//                    `).join('')}
//                </div>
//                <div class="no-results-message" id="alternative-no-results" style="display:none;">
//                    <i class="fa fa-search"></i>
//                    <p>No alternative products found</p>
//                </div>
//            </div>
//            <div class="alternative-footer">
//                <div class="alternative-footer-info">
//                    <i class="fa fa-info-circle"></i>
//                    <span>Showing ${products.length} alternative product${products.length !== 1 ? 's' : ''}</span>
//                </div>
//            </div>
//        `;
//    },
//
//    _attachAlternativeModalEvents(overlay, products) {
//        const searchInput = overlay.querySelector('#alternative-search-input');
//        const searchCount = overlay.querySelector('#alternative-search-count');
//        const grid = overlay.querySelector('#alternative-products-grid');
//        const noResults = overlay.querySelector('#alternative-no-results');
//        const cards = overlay.querySelectorAll('.alternative-product-card');
//        const filterBtns = overlay.querySelectorAll('.filter-btn');
//
//        let currentProducts = Array.from(cards);
//
//        // Filter functionality
//        filterBtns.forEach(btn => {
//            btn.addEventListener('click', () => {
//                filterBtns.forEach(b => b.classList.remove('active'));
//                btn.classList.add('active');
//
//                const filter = btn.dataset.filter;
//                const visibleCards = Array.from(cards).filter(card => card.style.display !== 'none');
//
//                switch(filter) {
//                    case 'all':
//                        cards.forEach(card => card.style.display = '');
//                        break;
//                    case 'in-stock':
//                        cards.forEach(card => {
//                            card.style.display = card.dataset.inStock === 'true' ? '' : 'none';
//                        });
//                        break;
//                    case 'price-low':
//                        const sortedLow = Array.from(cards).sort((a, b) =>
//                            parseFloat(a.dataset.price) - parseFloat(b.dataset.price)
//                        );
//                        grid.innerHTML = '';
//                        sortedLow.forEach(card => grid.appendChild(card));
//                        break;
//                    case 'price-high':
//                        const sortedHigh = Array.from(cards).sort((a, b) =>
//                            parseFloat(b.dataset.price) - parseFloat(a.dataset.price)
//                        );
//                        grid.innerHTML = '';
//                        sortedHigh.forEach(card => grid.appendChild(card));
//                        break;
//                }
//
//                this._updateVisibility(grid, noResults, cards);
//            });
//        });
//
//        // Search functionality
//        searchInput.addEventListener('input', (e) => {
//            const query = e.target.value.toLowerCase().trim();
//            let visibleCount = 0;
//
//            cards.forEach(card => {
//                const productName = card.dataset.productName;
//                const isVisible = !query || productName.includes(query);
//
//                if (isVisible && card.style.display !== 'none') {
//                    card.style.display = '';
//                    visibleCount++;
//                } else if (!isVisible) {
//                    card.style.display = 'none';
//                }
//            });
//
//            if (query) {
//                searchCount.textContent = `${visibleCount} result${visibleCount !== 1 ? 's' : ''}`;
//                searchCount.style.display = 'inline-block';
//            } else {
//                searchCount.style.display = 'none';
//            }
//
//            this._updateVisibility(grid, noResults, cards);
//        });
//
//        // Compare buttons
//        const compareBtns = overlay.querySelectorAll('.alternative-compare-btn');
//        compareBtns.forEach(btn => {
//            btn.addEventListener('click', (e) => {
//                e.stopPropagation();
//                const productId = btn.dataset.productId;
//                this._compareProducts(productId);
//            });
//        });
//
//        // Close handlers
//        overlay.addEventListener('click', (e) => {
//            if (e.target === overlay) overlay.remove();
//        });
//
//        document.addEventListener('keydown', (e) => {
//            if (e.key === 'Escape') overlay.remove();
//        });
//    },
//
//    _updateVisibility(grid, noResults, cards) {
//        const visibleCount = Array.from(cards).filter(card =>
//            card.style.display !== 'none'
//        ).length;
//
//        if (visibleCount === 0) {
//            grid.style.display = 'none';
//            noResults.style.display = 'flex';
//        } else {
//            grid.style.display = 'grid';
//            noResults.style.display = 'none';
//        }
//    },
//
//    // ========================================
//    // HELPER METHODS
//    // ========================================
//    async _addToCart(productId, button) {
//        const originalHTML = button.innerHTML;
//        button.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
//        button.disabled = true;
//
//        try {
//            const response = await fetch('/shop/cart/update', {
//                method: 'POST',
//                headers: { 'Content-Type': 'application/json' },
//                body: JSON.stringify({
//                    jsonrpc: "2.0",
//                    method: "call",
//                    params: {
//                        product_id: parseInt(productId),
//                        add_qty: 1
//                    }
//                })
//            });
//
//            if (!response.ok) throw new Error('Failed to add to cart');
//
//            button.innerHTML = '<i class="fa fa-check"></i> Added';
//            button.classList.add('success');
//            this._showNotification('Product added to cart successfully', 'success');
//
//            setTimeout(() => {
//                button.innerHTML = originalHTML;
//                button.disabled = false;
//                button.classList.remove('success');
//            }, 2000);
//
//        } catch (err) {
//            console.error('Error adding to cart:', err);
//            button.innerHTML = originalHTML;
//            button.disabled = false;
//            this._showNotification('Failed to add product to cart', 'error');
//        }
//    },
//
//    _compareProducts(productId) {
//        // Trigger the existing compare functionality
//        const compareBtn = document.querySelector('.pxm-btn-secondary');
//        if (compareBtn && compareBtn.textContent.includes('Compare')) {
//            compareBtn.click();
//        }
//    },
//
//    _showNotification(message, type = 'info') {
//        const notification = document.createElement('div');
//        notification.className = `pxm-notification pxm-notification-${type}`;
//
//        const iconMap = {
//            'success': 'check-circle',
//            'error': 'exclamation-circle',
//            'warning': 'exclamation-triangle',
//            'info': 'info-circle'
//        };
//
//        notification.innerHTML = `
//            <i class="fa fa-${iconMap[type] || 'info-circle'}"></i>
//            <span>${message}</span>
//        `;
//
//        document.body.appendChild(notification);
//
//        setTimeout(() => {
//            notification.classList.add('show');
//        }, 100);
//
//        setTimeout(() => {
//            notification.classList.remove('show');
//            setTimeout(() => notification.remove(), 300);
//        }, 3000);
//    }
//});




/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PXMProductAssociations = publicWidget.Widget.extend({
    selector: ".pxm-associations-wrapper",

    events: {
        "click .pxm-nav-btn": "_onNavClick",
        "mousedown .pxm-products-grid": "_onMouseDown",
        "mousemove .pxm-products-grid": "_onMouseMove",
        "mouseup .pxm-products-grid": "_onMouseUp",
        "mouseleave .pxm-products-grid": "_onMouseLeave",
    },

    start() {
//        this._initNavigationState();
        this._initScrollIndicators();
        this._bindScrollListeners();
        this._bindResize();
        this._initIntersectionObserver();
        return this._super(...arguments);
    },

    // ------------------------------------------------------------
    // Navigation arrows
    // ------------------------------------------------------------
    _onNavClick(ev) {
        const btn = ev.currentTarget;
        const targetId = btn.dataset.target;
        const container = document.getElementById(targetId);
        if (!container) return;

        const scrollAmount = 320;
        const isNext = btn.classList.contains("pxm-nav-next");

        container.scrollBy({
            left: isNext ? scrollAmount : -scrollAmount,
            behavior: "smooth",
        });

        setTimeout(() => this._updateNavButtons(container), 300);
    },

    _bindScrollListeners() {
        this.el.querySelectorAll(".pxm-products-grid").forEach(container => {
            container.addEventListener("scroll", () => {
                this._updateNavButtons(container);
                this._updateActiveIndicator(container);
            });
            this._updateNavButtons(container);
        });
    },

    _updateNavButtons(container) {
        const id = container.id;
        const prev = this.el.querySelector(`.pxm-nav-prev[data-target="${id}"]`);
        const next = this.el.querySelector(`.pxm-nav-next[data-target="${id}"]`);
        if (!prev || !next) return;

        const max = container.scrollWidth - container.clientWidth;

        prev.disabled = container.scrollLeft <= 0;
        next.disabled = container.scrollLeft >= max - 5;

        prev.style.opacity = prev.disabled ? "0.4" : "1";
        next.style.opacity = next.disabled ? "0.4" : "1";
    },

    // ------------------------------------------------------------
    // Scroll indicators
    // ------------------------------------------------------------
    _initScrollIndicators() {
        this.el.querySelectorAll(".pxm-products-grid").forEach(container => {
            const targetId = container.id;
            const indicator = this.el.querySelector(
                `.pxm-scroll-indicators[data-target="${targetId}"]`
            );
            if (!indicator) return;

            const pages = Math.ceil(container.scrollWidth / container.clientWidth);
            indicator.innerHTML = "";

            if (pages <= 1) {
                indicator.style.display = "none";
                return;
            }

            for (let i = 0; i < pages; i++) {
                const dot = document.createElement("span");
                dot.className = "pxm-indicator-dot";
                if (i === 0) dot.classList.add("active");

                dot.addEventListener("click", () => {
                    container.scrollTo({
                        left: i * container.clientWidth,
                        behavior: "smooth",
                    });
                });

                indicator.appendChild(dot);
            }
        });
    },

    _updateActiveIndicator(container) {
        const indicator = this.el.querySelector(
            `.pxm-scroll-indicators[data-target="${container.id}"]`
        );
        if (!indicator) return;

        const index = Math.round(container.scrollLeft / container.clientWidth);
        indicator.querySelectorAll(".pxm-indicator-dot").forEach((dot, i) => {
            dot.classList.toggle("active", i === index);
        });
    },

    // ------------------------------------------------------------
    // Drag scrolling
    // ------------------------------------------------------------
    _onMouseDown(ev) {
        const el = ev.currentTarget;
        el._drag = {
            active: true,
            startX: ev.pageX,
            scrollLeft: el.scrollLeft,
        };
        el.style.cursor = "grabbing";
    },

    _onMouseMove(ev) {
        const el = ev.currentTarget;
        if (!el._drag?.active) return;
        ev.preventDefault();
        const walk = (ev.pageX - el._drag.startX) * 2;
        el.scrollLeft = el._drag.scrollLeft - walk;
    },

    _onMouseUp(ev) {
        ev.currentTarget._drag = null;
        ev.currentTarget.style.cursor = "grab";
    },

    _onMouseLeave(ev) {
        ev.currentTarget._drag = null;
        ev.currentTarget.style.cursor = "grab";
    },

    // ------------------------------------------------------------
    // Resize
    // ------------------------------------------------------------
    _bindResize() {
        let timer;
        window.addEventListener("resize", () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                this._initScrollIndicators();
                this._bindScrollListeners();
            }, 250);
        });
    },

    // ------------------------------------------------------------
    // Intersection animation
    // ------------------------------------------------------------
    _initIntersectionObserver() {
        if (!("IntersectionObserver" in window)) return;

        const observer = new IntersectionObserver(entries => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    e.target.classList.add("pxm-visible");
                    observer.unobserve(e.target);
                }
            });
        }, { threshold: 0.1 });

        this.el.querySelectorAll(".pxm-section-block").forEach(el => {
            observer.observe(el);
        });
    },
});
