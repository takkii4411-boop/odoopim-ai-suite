
/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PXMShopDynamic = publicWidget.Widget.extend({
    selector: '#pxm-shop-wrapper',

    init() {
        this._super(...arguments);
        this.isLoading = false;
        this.currentRequest = null;
        this.currentPage = 1;
        this.limit = 20;
        this.currentView = 'grid';
        this.selectedFilters = {
            family_ids: [],
            category_ids: [],
            brand_ids: [],
            search: ''
        };
    },

    start() {
        console.log('PXM Shop Widget Started');
        this._setupSkeleton();
        this._bindFilterHandlers();
        this._bindSearchHandler();
        this._bindMobileFilterToggle();
        this._bindViewToggle();
        this._bindMobileFilterCollapse();
        this._loadProducts();
        return this._super(...arguments);
    },

    // =================================================================
    // MOBILE FILTER COLLAPSE HANDLERS
    // =================================================================
    _bindMobileFilterCollapse() {
        document.querySelectorAll('.pxm-mobile-section-header').forEach(header => {
            header.addEventListener('click', function() {
                const icon = this.querySelector('.pxm-mobile-chevron');
                if (icon) {
                    setTimeout(() => {
                        const target = this.getAttribute('data-bs-target');
                        const collapseElement = document.querySelector(target);
                        if (collapseElement && collapseElement.classList.contains('show')) {
                            icon.style.transform = 'rotate(180deg)';
                        } else {
                            icon.style.transform = 'rotate(0deg)';
                        }
                    }, 100);
                }
            });
        });
    },

    // =================================================================
    // VIEW TOGGLE (GRID / LIST)
    // =================================================================
    _bindViewToggle() {
        const gridBtn = document.getElementById('gridViewBtn');
        const listBtn = document.getElementById('listViewBtn');

        if (gridBtn) {
            gridBtn.addEventListener('click', () => {
                this.currentView = 'grid';
                gridBtn.classList.add('active');
                if (listBtn) listBtn.classList.remove('active');
                if (this.lastData) {
                    this._renderProducts(this.lastData);
                }
            });
        }

        if (listBtn) {
            listBtn.addEventListener('click', () => {
                this.currentView = 'list';
                listBtn.classList.add('active');
                if (gridBtn) gridBtn.classList.remove('active');
                if (this.lastData) {
                    this._renderProducts(this.lastData);
                }
            });
        }
    },

    // =================================================================
    // SKELETON LOADER
    // =================================================================
    _setupSkeleton() {
        const container = document.getElementById('productContainer');
        if (!container) return;

        const skeletonHTML = Array(8).fill().map(() => `
            <div class="col-12 col-md-4 col-lg-3 mb-4">
                <div class="pxm-product-card-modern skeleton-card h-100">
                    <div class="skeleton-image"></div>
                    <div class="p-3">
                        <div class="skeleton-line short mb-2"></div>
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line long mt-3"></div>
                    </div>
                </div>
            </div>
        `).join('');

        this.skeleton = document.createElement('div');
        this.skeleton.className = 'row';
        this.skeleton.innerHTML = skeletonHTML;
        this.skeleton.style.display = 'none';
        container.parentNode.insertBefore(this.skeleton, container);
    },

    _showSkeleton() {
        const container = document.getElementById('productContainer');
        if (container) container.style.opacity = '0.3';
        if (this.skeleton) this.skeleton.style.display = 'flex';
        this.isLoading = true;
    },

    _hideSkeleton() {
        const container = document.getElementById('productContainer');
        if (container) container.style.opacity = '1';
        if (this.skeleton) this.skeleton.style.display = 'none';
        this.isLoading = false;
    },

    // =================================================================
    // FILTER HANDLERS (FIXED)
    // =================================================================
    _bindFilterHandlers() {
        console.log('Binding filter handlers');

        // Use event delegation for better reliability
        document.addEventListener('change', (e) => {
            const checkbox = e.target;

            // Check if it's a filter checkbox
            if (!checkbox.classList.contains('pxm-filter-input') ||
                !checkbox.hasAttribute('data-filter')) {
                return;
            }

            const filterType = checkbox.getAttribute('data-filter');
            const filterId = parseInt(checkbox.getAttribute('data-id'));

            console.log(`Filter changed: ${filterType} - ${filterId} - ${checkbox.checked}`);

            // Sync all checkboxes with same filter type and ID
            this._syncCheckboxes(filterType, filterId, checkbox.checked);

            // Update filter state
            if (checkbox.checked) {
                if (!this.selectedFilters[`${filterType}_ids`].includes(filterId)) {
                    this.selectedFilters[`${filterType}_ids`].push(filterId);
                }
            } else {
                this.selectedFilters[`${filterType}_ids`] =
                    this.selectedFilters[`${filterType}_ids`].filter(id => id !== filterId);
            }

            console.log('Current filters:', this.selectedFilters);

            this.currentPage = 1;
            this._loadProducts();
        });

        // Filter tag removal
        document.addEventListener('click', (e) => {
            const closeBtn = e.target.closest('.pxm-filter-tag .btn-close');
            if (!closeBtn) return;

            e.preventDefault();
            const filterType = closeBtn.getAttribute('data-filter');
            const filterId = parseInt(closeBtn.getAttribute('data-id'));

            // Uncheck all checkboxes with this filter
            document.querySelectorAll(`input[data-filter="${filterType}"][data-id="${filterId}"]`).forEach(cb => {
                cb.checked = false;
            });

            this.selectedFilters[`${filterType}_ids`] =
                this.selectedFilters[`${filterType}_ids`].filter(id => id !== filterId);

            this.currentPage = 1;
            this._loadProducts();
        });

        // Clear all filters
        const clearAllBtn = document.querySelector('.pxm-clear-all-filters');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this._clearAllFilters();
            });
        }
    },

    _syncCheckboxes(filterType, filterId, checked) {
        const selector = `input[data-filter="${filterType}"][data-id="${filterId}"]`;
        document.querySelectorAll(selector).forEach(cb => {
            cb.checked = checked;
        });
    },

    _bindSearchHandler() {
        const searchInput = document.getElementById('pxmSearchInput') ||
                          document.querySelector('input[name="search"]');

        if (!searchInput) {
            console.warn('Search input not found');
            return;
        }

        console.log('Search handler bound');

        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const searchValue = e.target.value.trim();

            console.log('Search input:', searchValue);

            searchTimeout = setTimeout(() => {
                this.selectedFilters.search = searchValue;
                this.currentPage = 1;
                console.log('Executing search:', searchValue);
                this._loadProducts();
            }, 600);
        });

        // Also handle Enter key
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(searchTimeout);
                this.selectedFilters.search = e.target.value.trim();
                this.currentPage = 1;
                this._loadProducts();
            }
        });
    },

    _bindMobileFilterToggle() {
        const toggleBtn = document.getElementById('pxmMobileFilterToggle');
        const closeBtn = document.getElementById('pxmMobileFilterClose');
        const applyBtn = document.getElementById('pxmMobileFilterApply');
        const panel = document.getElementById('pxmMobileFilterPanel');
        const backdrop = panel ? panel.querySelector('.pxm-mobile-filter-backdrop') : null;

        console.log('Mobile filter elements:', {toggleBtn, closeBtn, applyBtn, panel, backdrop});

        const openPanel = () => {
            if (panel) {
                console.log('Opening mobile filter panel');
                panel.classList.add('show');
                document.body.classList.add('filter-open');
            }
        };

        const closePanel = () => {
            if (panel) {
                console.log('Closing mobile filter panel');
                panel.classList.remove('show');
                document.body.classList.remove('filter-open');
            }
        };

        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                openPanel();
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                closePanel();
            });
        }

        if (applyBtn) {
            applyBtn.addEventListener('click', (e) => {
                e.preventDefault();
                closePanel();
            });
        }

        // Close on backdrop click
        if (backdrop) {
            backdrop.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                closePanel();
            });
        }
    },

    _clearAllFilters() {
        console.log('Clearing all filters');

        this.selectedFilters = {
            family_ids: [],
            category_ids: [],
            brand_ids: [],
            search: ''
        };

        // Uncheck all filter checkboxes
        document.querySelectorAll('.pxm-filter-input').forEach(cb => {
            cb.checked = false;
        });

        // Clear search input
        const searchInput = document.getElementById('pxmSearchInput') ||
                          document.querySelector('input[name="search"]');
        if (searchInput) searchInput.value = '';

        this.currentPage = 1;
        this._loadProducts();
    },

    // =================================================================
    // MAIN: LOAD PRODUCTS VIA AJAX
    // =================================================================
    async _loadProducts(page = null) {
        if (this.isLoading) {
            console.log('Already loading, skipping...');
            return;
        }

        if (page !== null) this.currentPage = page;

        console.log('Loading products with filters:', this.selectedFilters);

        this._showSkeleton();

        // Abort previous request
        if (this.currentRequest) {
            this.currentRequest.abort();
        }
        this.currentRequest = new AbortController();

        const params = {
            ...this.selectedFilters,
            page: this.currentPage,
            limit: this.limit
        };

        console.log('Request params:', params);

        try {
            const response = await fetch('/pxm/shop/filter_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: params
                }),
                signal: this.currentRequest.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Server response:', result);

            const data = result.result;

            if (data.success) {
                this.lastData = data;
                this._renderProducts(data);
                this._updateFilterTags();
                this._updatePagination(data);
                this._updateURL();
            } else {
                console.error('Filter failed:', data.error);
                this._showError(data.error);
            }

        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error("Failed to load products:", err);
                this._showError(err.message);
            }
        } finally {
            this._hideSkeleton();
            this.currentRequest = null;
        }
    },

    // =================================================================
    // RENDER PRODUCTS
    // =================================================================
    _renderProducts(data) {
        const container = document.getElementById('productContainer');
        if (!container) return;

        const { products, total_products } = data;

        // Update product count header
        const countHeader = document.querySelector('.pxm-products-header');
        if (countHeader) {
            const hasFilters = this.selectedFilters.family_ids.length > 0 ||
                             this.selectedFilters.category_ids.length > 0 ||
                             this.selectedFilters.brand_ids.length > 0 ||
                             this.selectedFilters.search !== '';

            if (hasFilters) {
                countHeader.style.display = 'block';
                countHeader.textContent = `${total_products} Product${total_products !== 1 ? 's' : ''} Found`;
            } else {
                countHeader.style.display = 'none';
            }
        }

        // No products found
        if (!products || products.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa fa-search-minus text-muted" style="font-size:64px;"></i>
                    <h5 class="mt-4 text-muted">No products found</h5>
                    <p class="text-muted">Try adjusting your filters or search keywords.</p>
                </div>
            `;
            return;
        }

        // Render products based on view mode
        if (this.currentView === 'list') {
            const productsHTML = products.map(p => this._generateProductListItem(p)).join('');
            container.innerHTML = `<div class="pxm-list-view">${productsHTML}</div>`;
        } else {
            const productsHTML = products.map(p => this._generateProductCard(p)).join('');
            container.innerHTML = `<div class="row">${productsHTML}</div>`;
        }
    },

    _generateProductCard(product) {
        const availability = product.dynamic_values?.Availability || '';
        let availabilityHTML = '';

        const availabilityMap = {
            'In Stock': { class: 'success', icon: 'check-circle' },
            'Out of Stock': { class: 'danger', icon: 'times-circle' },
            'Coming Soon': { class: 'warning', icon: 'exclamation-triangle' },
            'Discontinued': { class: 'info', icon: 'clock-o' }
        };

        const availInfo = availabilityMap[availability] || { class: 'default', icon: 'info-circle' };

        availabilityHTML = `
            <div class="pxm-availability-ribbon pxm-ribbon-${availInfo.class}">
                <i class="fa fa-${availInfo.icon}"></i>
                <span class="pxm-ribbon-text">${availability || 'Not Updated'}</span>
            </div>
        `;

        const imageUrl = product.image_1920
            ? `data:image/png;base64,${product.image_1920}`
            : '/images/NoImage.jpg';

         // Extract currency symbol from price_html (₹, $, €, etc.)
            const currencySymbol = product.price_html
                ? product.price_html.replace(/[0-9.,\s]/g, '')
                : '';

            let dynamicPricesHTML = '';

            for (const [label, value] of Object.entries(product.dynamic_values || {})) {
                if (label === "Price per Meter" && value) {

                    if (Array.isArray(value)) {
                        dynamicPricesHTML = value
                            .filter(v => v)
                            .map(v => `
                                <strong>
                                    ${currencySymbol}${parseFloat(v).toFixed(2)}
                                </strong>
                            `)
                            .join(', ');
                    } else {
                        dynamicPricesHTML = `
                            <strong>
                                ${currencySymbol}${parseFloat(value).toFixed(2)}
                            </strong>
                        `;
                    }
                }
            }

            // Fallback to standard product price
            if (!dynamicPricesHTML && product.price_html) {
                dynamicPricesHTML = `<strong>${product.price_html}</strong>`;
            }

        return `
            <div class="col-12 col-md-4 col-lg-3 mb-4 product-item">
                <div class="pxm-product-card-modern">

                    <a href="${product.url}" class="pxm-image-wrapper">
                        <img src="${imageUrl}"
                             alt="${product.name}"
                             class="pxm-product-image"
                             onerror="this.src='/images/NoImage.jpg'">
                    </a>

                    <div class="pxm-card-content">

                        <div class="d-flex justify-content-between align-items-center mb-2">
                            ${product.default_code ? `<div class="pxm-sku">${product.default_code}</div>` : ''}

                            ${product.variant_count > 1 ? `
                                <div class="text-product-variant-counts">
                                    <i class="fa fa-cubes"></i> ${product.variant_count} variants
                                </div>
                            ` : ''}
                        </div>

                        <h5 class="pxm-product-title">
                            <a href="${product.url}">${product.name}</a>
                        </h5>

                        <div class="pxm-desc-clamp">
                            ${product.description_sale || ''}
                        </div>

                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            <div>${availabilityHTML}</div>
                            <div class="text-end">
                                ${dynamicPricesHTML || `<span class="text-muted small">Price N/A</span>`}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        `;
    },



    _generateProductListItem(product) {
    const availability = product.dynamic_values?.Availability || '';

    const availabilityMap = {
        'In Stock': { class: 'success', icon: 'check-circle' },
        'Out of Stock': { class: 'danger', icon: 'times-circle' },
        'Coming Soon': { class: 'warning', icon: 'exclamation-triangle' },
        'Discontinued': { class: 'info', icon: 'clock-o' }
    };

    const availInfo = availabilityMap[availability] || {
        class: 'secondary',
        icon: 'info-circle'
    };

    const availabilityHTML = `
        <span class="badge bg-${availInfo.class}" style="font-size:12px;">
            <i class="fa fa-${availInfo.icon} me-1"></i>
            ${availability || 'Not Updated'}
        </span>
    `;

    const imageUrl = product.image_1920
        ? `data:image/png;base64,${product.image_1920}`
        : '/images/NoImage.jpg';

    /* ===============================
       PRICE WITH CURRENCY (LIST)
    =============================== */

    const currencySymbol = product.price_html
        ? product.price_html.replace(/[0-9.,\s]/g, '')
        : '';

    let dynamicPricesHTML = '';

    for (const [label, value] of Object.entries(product.dynamic_values || {})) {
        if (label === 'Price per Meter' && value) {
            if (Array.isArray(value)) {
                dynamicPricesHTML = value
                    .filter(v => v)
                    .map(v => `${currencySymbol}${parseFloat(v).toFixed(2)}`)
                    .join(', ');
            } else {
                dynamicPricesHTML = `${currencySymbol}${parseFloat(value).toFixed(2)}`;
            }
        }
    }

    if (!dynamicPricesHTML && product.price_html) {
        dynamicPricesHTML = product.price_html;
    }

    /* ===============================
       GRID-STYLED LIST VIEW
    =============================== */

    return `
        <a href="${product.url}"
           class="pxm-list-item d-block text-decoration-none text-dark
                  border rounded mb-3 p-3">

            <div class="row align-items-center g-3">

                <!-- IMAGE -->
                <div class="col-12 col-md-2 text-center">
                    <img src="${imageUrl}"
                         alt="${product.name}"
                         class="img-fluid rounded"
                         style="max-height:120px;"
                         onerror="this.src='/images/NoImage.jpg'">
                </div>

                <!-- DETAILS -->
                <div class="col-12 col-md-7">

                    ${product.default_code ? `
                        <span class="pxm-sku"
                              style="font-size:12px;">
                            ${product.default_code}
                        </span>
                    ` : ''}

                    <div class="fw-bold"
                         style="font-size:16px; line-height:1.3;">
                        ${product.name}
                    </div>

                    <!-- DESCRIPTION (3 LINE CLAMP) -->
                    <div class="text-muted mt-1"
                         style="
                            font-size:14px;
                            display:-webkit-box;
                            -webkit-line-clamp:3;
                            -webkit-box-orient:vertical;
                            overflow:hidden;
                         ">
                        ${product.description_sale || ''}
                    </div>

                    <div class="mt-2">
                        ${availabilityHTML}
                    </div>
                </div>

                <!-- PRICE -->
                <div class="col-12 col-md-3 text-md-end mt-3 mt-md-0">
                    <div class="fw-bold"
                         style="font-size:18px;">
                        ${dynamicPricesHTML || '<span class="text-muted">Price N/A</span>'}
                    </div>

                    ${product.variant_count > 1 ? `
                        <div class="text-muted small mt-1">
                            <i class="fa fa-cubes me-1"></i>
                            ${product.variant_count} variants
                        </div>
                    ` : ''}
                </div>

            </div>
        </a>
    `;
},


    // =================================================================
    // UPDATE FILTER TAGS
    // =================================================================
    _updateFilterTags() {
        const tagsContainer = document.querySelector('.pxm-active-filters');
        if (!tagsContainer) return;

        const tags = [];

        const getFilterName = (type, id) => {
            const checkbox = document.querySelector(`input[data-filter="${type}"][data-id="${id}"]`);
            if (!checkbox) return null;

            const label = checkbox.closest('label')?.querySelector('.pxm-filter-text') ||
                         checkbox.nextElementSibling;
            return label ? label.textContent.trim() : null;
        };

        const filterConfig = [
            { type: 'family', icon: 'folder-open', color: 'primary' },
            { type: 'category', icon: 'tags', color: 'info' },
            { type: 'brand', icon: 'industry', color: 'success' }
        ];

        filterConfig.forEach(({ type, icon, color }) => {
            this.selectedFilters[`${type}_ids`].forEach(id => {
                const name = getFilterName(type, id);
                if (name) {
                    tags.push(`
                        <span class="bg-${color} me-2 mb-2 pxm-filter-tag">
                            <i class="fa fa-${icon} me-1"></i>
                            ${name}
                            <button type="button" class="btn-close btn-close-white ms-2"
                                    data-filter="${type}" data-id="${id}"
                                    aria-label="Close"></button>
                        </span>
                    `);
                }
            });
        });

        tagsContainer.innerHTML = tags.join('');
    },

    // =================================================================
    // UPDATE PAGINATION
    // =================================================================
    _updatePagination(data) {
        const paginationContainer = document.querySelector('.pxm-pagination');
        if (!paginationContainer) return;

        const { current_page, total_pages, has_prev, has_next } = data;

        if (total_pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        const paginationHTML = `
            <nav class="enhanced-pager-container" aria-label="Page navigation">
                <ul class="enhanced-pager">
                    <li class="pager-item ${!has_prev ? 'disabled' : ''}">
                        <a class="pager-link" href="#" data-page="${current_page - 1}">
                            <i class="fa fa-chevron-left"></i>
                        </a>
                    </li>
                    <li class="pager-item active">
                        <span class="pager-link">
                            Page <strong>${current_page}</strong> of <strong>${total_pages}</strong>
                        </span>
                    </li>
                    <li class="pager-item ${!has_next ? 'disabled' : ''}">
                        <a class="pager-link" href="#" data-page="${current_page + 1}">
                            <i class="fa fa-chevron-right"></i>
                        </a>
                    </li>
                </ul>
            </nav>
        `;

        paginationContainer.innerHTML = paginationHTML;

        paginationContainer.querySelectorAll('.pager-link').forEach(link => {
            const parent = link.closest('li');
            if (parent.classList.contains('disabled') || parent.classList.contains('active')) return;

            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.getAttribute('data-page'));
                this._loadProducts(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    },

    // =================================================================
    // UPDATE URL
    // =================================================================
    _updateURL() {
        const params = new URLSearchParams();

        if (this.selectedFilters.search) {
            params.append('search', this.selectedFilters.search);
        }

        this.selectedFilters.family_ids.forEach(id => params.append('family_ids', id));
        this.selectedFilters.category_ids.forEach(id => params.append('category_ids', id));
        this.selectedFilters.brand_ids.forEach(id => params.append('brand_ids', id));

        if (this.currentPage > 1) {
            params.append('page', this.currentPage);
        }

        const newUrl = `/pxm/shop${params.toString() ? '?' + params.toString() : ''}`;
        window.history.pushState({}, '', newUrl);
    },

    _showError(message) {
        const container = document.getElementById('productContainer');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa fa-exclamation-triangle text-danger" style="font-size:64px;"></i>
                    <h5 class="mt-4 text-danger">Failed to load products</h5>
                    <p class="text-muted">${message || 'Please try again later.'}</p>
                </div>
            `;
        }
    }
});
