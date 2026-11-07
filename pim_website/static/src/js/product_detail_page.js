///** @odoo-module **/
//
//import publicWidget from "@web/legacy/js/public/public_widget";
//
//publicWidget.registry.PXMProductGallery = publicWidget.Widget.extend({
//    selector: ".product-image-wrapper",
//
//    start() {
//        this._initGallery();
//        this._attachShareHandler();
//        this._attachCompareHandler();
//        return this._super(...arguments);
//    },
//
//    // ========================================
//    // SHARE BUTTON POPUP
//    // ========================================
//    _attachShareHandler() {
//        const shareBtn = document.querySelector('#pxm-share-btn');
//        if (!shareBtn) return;
//
//        shareBtn.addEventListener('click', (ev) => {
//            ev.preventDefault();
//
//            const pageUrl = encodeURIComponent(window.location.href);
//            const pageTitle = encodeURIComponent(document.title);
//
//            const shareLinks = [
//                { name: 'Facebook', url: `https://www.facebook.com/sharer/sharer.php?u=${pageUrl}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>', color: '#1877F2' },
//                { name: 'Twitter', url: `https://twitter.com/intent/tweet?url=${pageUrl}&text=${pageTitle}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>', color: '#000000' },
//                { name: 'LinkedIn', url: `https://www.linkedin.com/shareArticle?mini=true&url=${pageUrl}&title=${pageTitle}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>', color: '#0A66C2' },
//                { name: 'WhatsApp', url: `https://api.whatsapp.com/send?text=${pageTitle}%20${pageUrl}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>', color: '#25D366' },
//                { name: 'Email', url: `mailto:?subject=${pageTitle}&body=${pageUrl}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>', color: '#EA4335' }
//            ];
//
//            const overlay = this._createShareOverlay(shareLinks);
//            document.body.appendChild(overlay);
//
//            overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
//            document.addEventListener('keydown', e => { if (e.key === 'Escape') overlay.remove(); });
//        });
//    },
//
//    _createShareOverlay(shareLinks) {
//        const overlay = document.createElement('div');
//        overlay.id = 'pxm-share-overlay';
//        overlay.className = 'pxm-overlay';
//
//        const popup = document.createElement('div');
//        popup.className = 'pxm-share-popup';
//
//        let popupHtml = `
//            <div class="pxm-share-header">
//                <h3 class="pxm-share-title">Share this page</h3>
//                <button class="pxm-close-btn" onclick="this.closest('.pxm-overlay').remove()">
//                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
//                        <line x1="18" y1="6" x2="6" y2="18"></line>
//                        <line x1="6" y1="6" x2="18" y2="18"></line>
//                    </svg>
//                </button>
//            </div>
//            <div class="pxm-share-body">
//                <div class="pxm-share-grid">`;
//
//        shareLinks.forEach(link => {
//            popupHtml += `
//                <a href="${link.url}" target="_blank" class="pxm-share-item" style="--share-color:${link.color};"
//                   onclick="setTimeout(()=>this.closest('.pxm-overlay').remove(),300)">
//                    <div class="pxm-share-icon">${link.icon}</div>
//                    <span class="pxm-share-name">${link.name}</span>
//                </a>`;
//        });
//
//        popupHtml += `</div></div>`;
//        popup.innerHTML = popupHtml;
//        overlay.appendChild(popup);
//
//        return overlay;
//    },
//
//    // ========================================
//    // COMPARE HANDLER
//    // ========================================
//    _attachCompareHandler() {
//        const compareBtns = document.querySelectorAll('.pxm-btn-secondary');
//        compareBtns.forEach(btn => {
//            if (btn.textContent.trim().includes('Compare')) {
//                btn.addEventListener('click', (ev) => {
//                    ev.preventDefault();
//                    this._showCompareModal();
//                });
//            }
//        });
//    },
//
//    async _showCompareModal() {
//        const products = await this._fetchProducts();
//
//        if (!products || products.length === 0) {
//            this._showNotification('No products available for comparison', 'warning');
//            return;
//        }
//
//        const overlay = document.createElement('div');
//        overlay.id = 'pxm-compare-overlay';
//        overlay.className = 'pxm-overlay pxm-compare-overlay';
//
//        const modal = document.createElement('div');
//        modal.className = 'pxm-compare-modal';
//        modal.innerHTML = this._generateCompareModalHTML(products);
//
//        overlay.appendChild(modal);
//        document.body.appendChild(overlay);
//
//        this._attachCompareModalEvents(overlay, products);
//
//        // Auto-select current product
//        const currentProductId = document.querySelector('input[name="product_template_id"]')?.value;
//        if (currentProductId) {
//            setTimeout(() => {
//                const cb = overlay.querySelector(`.product-checkbox[data-product-id="${currentProductId}"]`);
//                if (cb && !cb.checked) {
//                    cb.checked = true;
//                    cb.dispatchEvent(new Event('change'));
//                }
//            }, 300);
//        }
//    },
//
//    async _fetchProducts() {
//        try {
//            const response = await fetch('/pxm/shop/compare_data', {
//                method: 'POST',
//                headers: { 'Content-Type': 'application/json' },
//                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} })
//            });
//
//            if (!response.ok) throw new Error('Failed to fetch products');
//
//            const result = await response.json();
//            const products = result.result?.products || [];
//
//            return products.map(p => ({
//                id: p.id,
//                name: p.name || 'Product',
//                price: p.price_html || '$0.00',
//                image: p.image_1920
//                    ? `data:image/png;base64,${p.image_1920}`
//                    : `/web/image/product.template/${p.id}/image_1920`,
//                url: `/pxm/product/${p.id}`,
//                specs: p.dynamic_values || {}
//            }));
//
//        } catch (err) {
//            console.error("Failed to load products:", err);
//            return this._getFallbackProduct();
//        }
//    },
//
//    _getFallbackProduct() {
//        const name = document.querySelector('.product-title')?.textContent.trim() || 'Current Product';
//        const price = document.querySelector('.pxm-value-text')?.textContent || '$0.00';
//        const image = document.querySelector('#mainProductImage')?.src || '/images/NoImage.jpg';
//
//        return [{
//            id: Date.now(),
//            name,
//            price,
//            image,
//            url: window.location.href,
//            specs: this._extractCurrentProductSpecs()
//        }];
//    },
//
//    _extractCurrentProductSpecs() {
//        const specs = {};
//        document.querySelectorAll('.pxm-attr-badge, .pxm-ribbon-text, .product-meta strong').forEach(el => {
//            const text = el.textContent.trim();
//            if (!text || ['$', '%', 'In Stock', 'Out of Stock'].some(t => text.includes(t))) return;
//            const labelEl = el.closest('.row, .col')?.querySelector('small.text-muted');
//            const label = labelEl ? labelEl.textContent.replace(':', '').trim() : 'Detail';
//            if (text && text !== 'N/A') specs[label] = text;
//        });
//        return Object.keys(specs).length ? specs : { 'Status': 'In Stock' };
//    },
//
//    _generateCompareModalHTML(products) {
//        return `
//            <div class="compare-header">
//                <h2 class="compare-title">
//                    <i class="fa fa-balance-scale"></i>
//                    Compare Products
//                </h2>
//                <button class="pxm-close-btn" onclick="this.closest('.pxm-overlay').remove()">
//                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
//                        <line x1="18" y1="6" x2="6" y2="18"></line>
//                        <line x1="6" y1="6" x2="18" y2="18"></line>
//                    </svg>
//                </button>
//            </div>
//
//            <div class="compare-body">
//                <div class="product-selection">
//                    <div class="selection-header">
//                        <div class="selection-title">
//                            <i class="fa fa-check-circle"></i>
//                            Select Products
//                        </div>
//                        <span class="selection-hint">Choose 2-4 products to compare</span>
//                    </div>
//
//                    <!-- Search Bar -->
//                    <div class="product-search-container">
//                        <div class="search-input-wrapper">
//                            <i class="fa fa-search search-icon"></i>
//                            <input
//                                type="text"
//                                id="product-search-input"
//                                class="product-search-input"
//                                placeholder="Search products by name..."
//                                autocomplete="off"
//                            />
//                            <span class="search-results-count" id="search-results-count"></span>
//                        </div>
//                    </div>
//
//                    <!-- Alert -->
//                    <div id="compare-alert" class="compare-alert">
//                        <i class="fa fa-exclamation-triangle"></i>
//                        <span><strong>Maximum 4 products allowed!</strong> Unselect a product to add another.</span>
//                    </div>
//
//                    <!-- Product Grid -->
//                    <div class="product-grid-wrapper" id="product-grid-wrapper">
//                        <div class="product-grid" id="product-grid">
//                            ${products.map(p => `
//                                <div class="product-card" data-product-id="${p.id}" data-product-name="${p.name.toLowerCase()}">
//                                    <div class="product-checkbox-wrapper">
//                                        <input type="checkbox" class="product-checkbox" data-product-id="${p.id}" id="product-${p.id}">
//                                        <label for="product-${p.id}" class="checkbox-label"></label>
//                                    </div>
//                                    <img src="${p.image}" alt="${p.name}" class="product-image" loading="lazy" onerror="this.src='/images/NoImage.jpg'">
//                                    <div class="product-info">
//                                        <div class="compare-product-title" title="${p.name}">${p.name}</div>
//                                    </div>
//                                </div>
//                            `).join('')}
//                        </div>
//                        <div class="no-results-message" style="display:none;">
//                            <i class="fa fa-search"></i>
//                            <p>No products found</p>
//                        </div>
//                    </div>
//                </div>
//
//                <!-- Comparison Table -->
//                <div id="comparison-section" class="comparison-section">
//                    <div id="comparison-placeholder" class="comparison-placeholder">
//                        <i class="fa fa-balance-scale"></i>
//                        <h4>Select 2-4 Products to Compare</h4>
//                        <p>Click on product cards above to add them to the comparison</p>
//                    </div>
//                    <div id="comparison-table-container" class="comparison-table-container" style="display:none;">
//                        <div class="comparison-table-header">
//                            <h3>Product Comparison</h3>
//                        </div>
//                        <div class="comparison-table-wrapper">
//                            <table class="comparison-table" id="comparison-table"></table>
//                        </div>
//                    </div>
//                </div>
//            </div>
//
//            <div class="compare-footer">
//                <div class="footer-left">
//                    <span class="selected-count">
//                        <i class="fa fa-check-circle"></i>
//                        <strong id="selected-count-num">0</strong> products selected
//                    </span>
//                </div>
//                <div class="footer-actions">
//                    <button class="pxm-btn pxm-btn-clear" id="clear-selection-btn" style="display:none;">
//                        <i class="fa fa-times-circle"></i>
//                        Clear Selection
//                    </button>
//                    <button class="pxm-btn pxm-btn-primary" id="select-fields-btn" style="display:none;">
//                        <i class="fa fa-filter"></i>
//                        Select Fields
//                    </button>
//                </div>
//            </div>
//        `;
//    },
//
//    _attachCompareModalEvents(overlay, products) {
//        const selectedProducts = new Set();
//        const checkboxes = overlay.querySelectorAll('.product-checkbox');
//        const cards = overlay.querySelectorAll('.product-card');
//        const countSpan = overlay.querySelector('#selected-count-num');
//        const table = overlay.querySelector('#comparison-table');
//        const tableContainer = overlay.querySelector('#comparison-table-container');
//        const placeholder = overlay.querySelector('#comparison-placeholder');
//        const alertBox = overlay.querySelector('#compare-alert');
//        const searchInput = overlay.querySelector('#product-search-input');
//        const searchCount = overlay.querySelector('#search-results-count');
//        const gridWrapper = overlay.querySelector('#product-grid-wrapper');
//        const clearBtn = overlay.querySelector('#clear-selection-btn');
//        const selectFieldsBtn = overlay.querySelector('#select-fields-btn');
//
//        // Update comparison display
//        const updateComparison = () => {
//            const selected = products.filter(p => selectedProducts.has(p.id));
//
//            if (selected.length >= 2) {
//                placeholder.style.display = 'none';
//                tableContainer.style.display = 'block';
//                this._showComparisonTable(table, selected);
//
//                if (selected.length === 2) {
//                    setTimeout(() => {
//                        tableContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
//                    }, 300);
//                }
//            } else {
//                tableContainer.style.display = 'none';
//                placeholder.style.display = 'flex';
//            }
//        };
//
//        // Toggle buttons visibility
//        const updateButtonsVisibility = () => {
//            const count = selectedProducts.size;
//            clearBtn.style.display = count > 0 ? 'inline-flex' : 'none';
//            selectFieldsBtn.style.display = count >= 2 ? 'inline-flex' : 'none';
//        };
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
//            const grid = overlay.querySelector('#product-grid');
//            const noResultsMsg = overlay.querySelector('.no-results-message');
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
//                noResultsMsg.style.display = 'flex';
//                noResultsMsg.querySelector('p').textContent = `No products found matching "${query}"`;
//            } else {
//                grid.style.display = 'grid';
//                noResultsMsg.style.display = 'none';
//            }
//        });
//
//        // Checkbox change handler
//        checkboxes.forEach(cb => {
//            cb.addEventListener('change', (e) => {
//                const id = parseInt(e.target.dataset.productId);
//                const card = overlay.querySelector(`.product-card[data-product-id="${id}"]`);
//
//                if (e.target.checked) {
//                    if (selectedProducts.size >= 4) {
//                        e.target.checked = false;
//                        alertBox.style.display = 'flex';
//                        setTimeout(() => { alertBox.style.display = 'none'; }, 4000);
//                        return;
//                    }
//                    selectedProducts.add(id);
//                    card.classList.add('selected');
//                } else {
//                    selectedProducts.delete(id);
//                    card.classList.remove('selected');
//                    alertBox.style.display = 'none';
//                }
//
//                countSpan.textContent = selectedProducts.size;
//                updateButtonsVisibility();
//                updateComparison();
//            });
//        });
//
//        // Card click handler
//        cards.forEach(card => {
//            card.addEventListener('click', (e) => {
//                if (e.target.classList.contains('product-checkbox') ||
//                    e.target.classList.contains('checkbox-label')) return;
//
//                const cb = card.querySelector('.product-checkbox');
//                cb.checked = !cb.checked;
//                cb.dispatchEvent(new Event('change'));
//            });
//        });
//
//        // Clear selection
//        clearBtn.addEventListener('click', () => {
//            selectedProducts.clear();
//            checkboxes.forEach(cb => {
//                cb.checked = false;
//                const card = overlay.querySelector(`.product-card[data-product-id="${cb.dataset.productId}"]`);
//                if (card) card.classList.remove('selected');
//            });
//            countSpan.textContent = '0';
//            updateButtonsVisibility();
//            updateComparison();
//        });
//
//        // Select fields button
//        selectFieldsBtn.addEventListener('click', () => {
//            this._showFieldSelector(products, selectedProducts, table);
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
//    _showFieldSelector(products, selectedProducts, table) {
//        const selected = products.filter(p => selectedProducts.has(p.id));
//        const allKeys = new Set();
//        selected.forEach(p => Object.keys(p.specs).forEach(k => allKeys.add(k)));
//
//        const overlay = document.createElement('div');
//        overlay.className = 'pxm-overlay pxm-field-overlay';
//
//        const popup = document.createElement('div');
//        popup.className = 'pxm-field-popup';
//
//        const fieldsArray = Array.from(allKeys).sort();
//
//        let html = `
//            <div class="pxm-popup-header">
//                <div class="pxm-popup-title">Select Fields to Compare</div>
//                <div class="pxm-popup-subtitle">Choose which fields you want to include in the comparison</div>
//            </div>
//
//            <div class="pxm-search-container">
//                <div class="pxm-search-box">
//                    <span class="pxm-search-icon"><i class="fa fa-search"></i></span>
//                    <input type="text" class="pxm-search-input" placeholder="Search fields..." id="field-search">
//                </div>
//            </div>
//
//            <div class="pxm-action-bar">
//                <span class="pxm-selected-count" id="selected-count">${fieldsArray.length} fields selected</span>
//                <div class="pxm-quick-actions">
//                    <button class="pxm-quick-btn" id="select-all">Select All</button>
//                    <button class="pxm-quick-btn" id="deselect-all">Clear All</button>
//                </div>
//            </div>
//
//            <div class="pxm-fields-container">`;
//
//        fieldsArray.forEach(field => {
//            html += `
//                <div class="pxm-field-item">
//                    <div class="pxm-checkbox-wrapper">
//                        <input type="checkbox" class="pxm-checkbox field-checkbox" value="${field}" checked id="field-${field.replace(/\s/g, '-')}">
//                    </div>
//                    <label for="field-${field.replace(/\s/g, '-')}" class="pxm-field-label">${field}</label>
//                </div>`;
//        });
//
//        html += `
//            </div>
//
//            <div class="pxm-popup-footer">
//                <button class="pxm-btn pxm-btn-secondary" id="cancel-fields-btn">Cancel</button>
//                <button class="pxm-btn pxm-btn-primary" id="apply-fields-btn">Apply Selection</button>
//            </div>
//        `;
//
//        popup.innerHTML = html;
//        overlay.appendChild(popup);
//        document.body.appendChild(overlay);
//
//        // Field selector events
//        const searchInput = popup.querySelector('#field-search');
//        const selectAllBtn = popup.querySelector('#select-all');
//        const deselectAllBtn = popup.querySelector('#deselect-all');
//        const cancelBtn = popup.querySelector('#cancel-fields-btn');
//        const applyBtn = popup.querySelector('#apply-fields-btn');
//        const checkboxes = popup.querySelectorAll('.field-checkbox');
//        const selectedCountSpan = popup.querySelector('#selected-count');
//        const fieldsContainer = popup.querySelector('.pxm-fields-container');
//
//        const updateSelectedCount = () => {
//            const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
//            selectedCountSpan.textContent = `${checkedCount} field${checkedCount !== 1 ? 's' : ''} selected`;
//        };
//
//        // Search fields
//        searchInput.addEventListener('input', (e) => {
//            const searchTerm = e.target.value.toLowerCase();
//            const fieldItems = fieldsContainer.querySelectorAll('.pxm-field-item');
//            let visibleCount = 0;
//
//            fieldItems.forEach(item => {
//                const label = item.querySelector('.pxm-field-label').textContent.toLowerCase();
//                if (label.includes(searchTerm)) {
//                    item.style.display = '';
//                    visibleCount++;
//                } else {
//                    item.style.display = 'none';
//                }
//            });
//
//            const existingEmpty = fieldsContainer.querySelector('.pxm-empty-state');
//            if (existingEmpty) existingEmpty.remove();
//
//            if (visibleCount === 0) {
//                const emptyState = document.createElement('div');
//                emptyState.className = 'pxm-empty-state';
//                emptyState.innerHTML = `
//                    <div class="pxm-empty-icon">🔍</div>
//                    <div class="pxm-empty-text">No fields found matching "${searchTerm}"</div>
//                `;
//                fieldsContainer.appendChild(emptyState);
//            }
//        });
//
//        // Select/Deselect all
//        selectAllBtn.addEventListener('click', () => {
//            const visibleCheckboxes = Array.from(checkboxes).filter(cb =>
//                cb.closest('.pxm-field-item').style.display !== 'none'
//            );
//            visibleCheckboxes.forEach(cb => cb.checked = true);
//            updateSelectedCount();
//        });
//
//        deselectAllBtn.addEventListener('click', () => {
//            const visibleCheckboxes = Array.from(checkboxes).filter(cb =>
//                cb.closest('.pxm-field-item').style.display !== 'none'
//            );
//            visibleCheckboxes.forEach(cb => cb.checked = false);
//            updateSelectedCount();
//        });
//
//        checkboxes.forEach(cb => {
//            cb.addEventListener('change', updateSelectedCount);
//        });
//
//        // Field item click
//        popup.querySelectorAll('.pxm-field-item').forEach(item => {
//            item.addEventListener('click', (e) => {
//                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'LABEL') {
//                    const checkbox = item.querySelector('.pxm-checkbox');
//                    checkbox.checked = !checkbox.checked;
//                    updateSelectedCount();
//                }
//            });
//        });
//
//        // Cancel
//        cancelBtn.addEventListener('click', () => overlay.remove());
//
//        // Apply
//        applyBtn.addEventListener('click', () => {
//            const checkedFields = Array.from(checkboxes)
//                .filter(cb => cb.checked)
//                .map(cb => cb.value);
//
//            if (checkedFields.length === 0) {
//                this._showNotification('Please select at least one field', 'warning');
//                return;
//            }
//
//            this._showComparisonTable(table, selected, checkedFields);
//            overlay.remove();
//        });
//
//        // Close on overlay click
//        overlay.addEventListener('click', (e) => {
//            if (e.target === overlay) overlay.remove();
//        });
//
//        // Close on Escape
//        const escapeHandler = (e) => {
//            if (e.key === 'Escape') {
//                overlay.remove();
//                document.removeEventListener('keydown', escapeHandler);
//            }
//        };
//        document.addEventListener('keydown', escapeHandler);
//    },
//
//    _showComparisonTable(table, products, fieldsFilter = null) {
//        if (products.length < 2) return;
//
//        let allKeys = new Set();
//        products.forEach(p => Object.keys(p.specs).forEach(k => allKeys.add(k)));
//
//        if (fieldsFilter && fieldsFilter.length > 0) {
//            allKeys = new Set(fieldsFilter);
//        }
//
//        const sortedKeys = Array.from(allKeys).sort();
//
//        let html = `
//            <thead>
//                <tr>
//                    <th class="field-column">Product Details</th>
//                    ${products.map(p => `
//                        <th class="product-column">
//                            <div class="product-header-content">
//                                <img src="${p.image}" alt="${p.name}" onerror="this.src='/images/NoImage.jpg'">
//                                <div class="product-header-info">
//                                    <div class="product-header-name">${p.name}</div>
//                                </div>
//                            </div>
//                        </th>
//                    `).join('')}
//                </tr>
//            </thead>
//            <tbody>
//                ${sortedKeys.map((key, index) => `
//                    <tr class="${index % 2 === 0 ? 'even-row' : 'odd-row'}">
//                        <td class="field-name">${key}</td>
//                        ${products.map(p => {
//                            const value = p.specs[key] || 'N/A';
//                            return `<td class="field-value">${value}</td>`;
//                        }).join('')}
//                    </tr>
//                `).join('')}
//            </tbody>
//        `;
//
//        table.innerHTML = html;
//        table.classList.add('active');
//    },
//
//    _showNotification(message, type = 'info') {
//        const notification = document.createElement('div');
//        notification.className = `pxm-notification pxm-notification-${type}`;
//        notification.innerHTML = `
//            <i class="fa fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
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
//    },
//
//    // ========================================
//    // GALLERY INITIALIZATION
//    // ========================================
//    _initGallery() {
//        const mainImg = this.el.querySelector("#mainProductImage");
//        const thumbs = Array.from(this.el.querySelectorAll(".thumb-item"));
//        if (!mainImg || !thumbs.length) return;
//
//        let currentIndex = 0;
//
//        const updateImage = (index) => {
//            const newSrc = thumbs[index].dataset.src || thumbs[index].src;
//            mainImg.src = newSrc;
//
//            thumbs.forEach(t => t.classList.remove("border-primary"));
//            thumbs[index].classList.add("border-primary");
//
//            const thumbEl = thumbs[index];
//            const carousel = this.el.querySelector(".thumbnail-carousel");
//            if (carousel) {
//                carousel.scrollTo({
//                    left: thumbEl.offsetLeft - (carousel.clientWidth / 2) + (thumbEl.offsetWidth / 2),
//                    behavior: "smooth"
//                });
//            }
//        };
//
//        thumbs.forEach((thumb, i) => {
//            thumb.addEventListener("click", () => {
//                currentIndex = i;
//                updateImage(i);
//            });
//        });
//
//        this.el.querySelector(".left-arrow")?.addEventListener("click", () => {
//            currentIndex = (currentIndex - 1 + thumbs.length) % thumbs.length;
//            updateImage(currentIndex);
//        });
//
//        this.el.querySelector(".right-arrow")?.addEventListener("click", () => {
//            currentIndex = (currentIndex + 1) % thumbs.length;
//            updateImage(currentIndex);
//        });
//
//        updateImage(0);
//    },
//});
//
//
//
//
//
//
//
//
//
//
//
//
//



/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PXMProductGallery = publicWidget.Widget.extend({
    selector: ".product-image-wrapper",

    start() {
        this._initGallery();
        this._attachShareHandler();
        this._attachCompareHandler();
        return this._super(...arguments);
    },

    // ========================================
    // SHARE BUTTON POPUP
    // ========================================
    _attachShareHandler() {
        const shareBtn = document.querySelector('#pxm-share-btn');
        if (!shareBtn) return;

        shareBtn.addEventListener('click', (ev) => {
            ev.preventDefault();

            const pageUrl = encodeURIComponent(window.location.href);
            const pageTitle = encodeURIComponent(document.title);

            const shareLinks = [
                { name: 'Facebook', url: `https://www.facebook.com/sharer/sharer.php?u=${pageUrl}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>', color: '#1877F2' },
                { name: 'Twitter', url: `https://twitter.com/intent/tweet?url=${pageUrl}&text=${pageTitle}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>', color: '#000000' },
                { name: 'LinkedIn', url: `https://www.linkedin.com/shareArticle?mini=true&url=${pageUrl}&title=${pageTitle}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>', color: '#0A66C2' },
                { name: 'WhatsApp', url: `https://api.whatsapp.com/send?text=${pageTitle}%20${pageUrl}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>', color: '#25D366' },
                { name: 'Email', url: `mailto:?subject=${pageTitle}&body=${pageUrl}`, icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>', color: '#EA4335' }
            ];

            const overlay = this._createShareOverlay(shareLinks);
            document.body.appendChild(overlay);

            overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
            document.addEventListener('keydown', e => { if (e.key === 'Escape') overlay.remove(); });
        });
    },

    _createShareOverlay(shareLinks) {
        const overlay = document.createElement('div');
        overlay.id = 'pxm-share-overlay';
        overlay.className = 'pxm-overlay';

        const popup = document.createElement('div');
        popup.className = 'pxm-share-popup';

        let popupHtml = `
            <div class="pxm-share-header">
                <h3 class="pxm-share-title">Share this page</h3>
                <button class="pxm-close-btn" onclick="this.closest('.pxm-overlay').remove()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="pxm-share-body">
                <div class="pxm-share-grid">`;

        shareLinks.forEach(link => {
            popupHtml += `
                <a href="${link.url}" target="_blank" class="pxm-share-item" style="--share-color:${link.color};"
                   onclick="setTimeout(()=>this.closest('.pxm-overlay').remove(),300)">
                    <div class="pxm-share-icon">${link.icon}</div>
                    <span class="pxm-share-name">${link.name}</span>
                </a>`;
        });

        popupHtml += `</div></div>`;
        popup.innerHTML = popupHtml;
        overlay.appendChild(popup);

        return overlay;
    },

    // ========================================
    // COMPARE HANDLER
    // ========================================
    _attachCompareHandler() {
        const compareBtns = document.querySelectorAll('.pxm-btn-secondary');
        compareBtns.forEach(btn => {
            if (btn.textContent.trim().includes('Compare')) {
                btn.addEventListener('click', (ev) => {
                    ev.preventDefault();
                    this._showCompareModal();
                });
            }
        });
    },

    async _showCompareModal() {
        const products = await this._fetchProducts();

        if (!products || products.length === 0) {
            this._showNotification('No products available for comparison', 'warning');
            return;
        }

        const overlay = document.createElement('div');
        overlay.id = 'pxm-compare-overlay';
        overlay.className = 'pxm-overlay pxm-compare-overlay';

        const modal = document.createElement('div');
        modal.className = 'pxm-compare-modal';
        modal.innerHTML = this._generateCompareModalHTML(products);

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        this._attachCompareModalEvents(overlay, products);

        // Auto-select current product
        const currentProductId = document.querySelector('input[name="product_template_id"]')?.value;
        if (currentProductId) {
            setTimeout(() => {
                const cb = overlay.querySelector(`.product-checkbox[data-product-id="${currentProductId}"]`);
                if (cb && !cb.checked) {
                    cb.checked = true;
                    cb.dispatchEvent(new Event('change'));
                }
            }, 300);
        }
    },

    async _fetchProducts() {
        try {
            const response = await fetch('/pxm/shop/compare_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} })
            });

            if (!response.ok) throw new Error('Failed to fetch products');

            const result = await response.json();
            const products = result.result?.products || [];

            return products.map(p => ({
                id: p.id,
                name: p.name || 'Product',
                price: p.price_html || '$0.00',
                image: p.image_1920
                    ? `data:image/png;base64,${p.image_1920}`
                    : `/web/image/product.template/${p.id}/image_1920`,
                url: `/pxm/product/${p.id}`,
                specs: p.dynamic_values || {}
            }));

        } catch (err) {
            console.error("Failed to load products:", err);
            return this._getFallbackProduct();
        }
    },

    _getFallbackProduct() {
        const name = document.querySelector('.product-title')?.textContent.trim() || 'Current Product';
        const price = document.querySelector('.pxm-value-text')?.textContent || '$0.00';
        const image = document.querySelector('#mainProductImage')?.src || '/images/NoImage.jpg';

        return [{
            id: Date.now(),
            name,
            price,
            image,
            url: window.location.href,
            specs: this._extractCurrentProductSpecs()
        }];
    },

    _extractCurrentProductSpecs() {
        const specs = {};
        document.querySelectorAll('.pxm-attr-badge, .pxm-ribbon-text, .product-meta strong').forEach(el => {
            const text = el.textContent.trim();
            if (!text || ['$', '%', 'In Stock', 'Out of Stock'].some(t => text.includes(t))) return;
            const labelEl = el.closest('.row, .col')?.querySelector('small.text-muted');
            const label = labelEl ? labelEl.textContent.replace(':', '').trim() : 'Detail';
            if (text && text !== 'N/A') specs[label] = text;
        });
        return Object.keys(specs).length ? specs : { 'Status': 'In Stock' };
    },

    _generateCompareModalHTML(products) {
        return `
            <div class="compare-header">
                <h2 class="compare-title">
                    <i class="fa fa-balance-scale"></i>
                    Compare Products
                </h2>
                <button class="pxm-close-btn" onclick="this.closest('.pxm-overlay').remove()">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>

            <div class="compare-body">
                <div class="product-selection">
                    <div class="selection-header">
                        <div class="selection-title">
                            <i class="fa fa-check-circle"></i>
                            Select Products
                        </div>
                        <span class="selection-hint">Choose 2-4 products to compare</span>
                    </div>

                    <!-- Search Bar -->
                    <div class="product-search-container">
                        <div class="search-input-wrapper">
                            <i class="fa fa-search search-icon"></i>
                            <input
                                type="text"
                                id="product-search-input"
                                class="product-search-input"
                                placeholder="Search products by name..."
                                autocomplete="off"
                            />
                            <span class="search-results-count" id="search-results-count"></span>
                        </div>
                    </div>

                    <!-- Alert -->
                    <div id="compare-alert" class="compare-alert">
                        <i class="fa fa-exclamation-triangle"></i>
                        <span><strong>Maximum 4 products allowed!</strong> Unselect a product to add another.</span>
                    </div>

                    <!-- Product Grid -->
                    <div class="product-grid-wrapper" id="product-grid-wrapper">
                        <div class="product-grid" id="product-grid">
                            ${products.map(p => `
                                <div class="product-card" data-product-id="${p.id}" data-product-name="${p.name.toLowerCase()}">
                                    <div class="product-checkbox-wrapper">
                                        <input type="checkbox" class="product-checkbox" data-product-id="${p.id}" id="product-${p.id}">
                                        <label for="product-${p.id}" class="checkbox-label"></label>
                                    </div>
                                    <img src="${p.image}" alt="${p.name}" class="product-image" loading="lazy" onerror="this.src='/images/NoImage.jpg'">
                                    <div class="product-info">
                                        <div class="compare-product-title" title="${p.name}">${p.name}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="no-results-message" style="display:none;">
                            <i class="fa fa-search"></i>
                            <p>No products found</p>
                        </div>
                    </div>
                </div>

                <!-- Comparison Table -->
                <div id="comparison-section" class="comparison-section">
                    <div id="comparison-placeholder" class="comparison-placeholder">
                        <i class="fa fa-balance-scale"></i>
                        <h4>Select 2-4 Products to Compare</h4>
                        <p>Click on product cards above to add them to the comparison</p>
                    </div>
                    <div id="comparison-table-container" class="comparison-table-container" style="display:none;">
                        <div class="comparison-table-header">
                            <h3>Product Comparison</h3>
                        </div>
                        <div class="comparison-table-wrapper">
                            <table class="comparison-table" id="comparison-table"></table>
                        </div>
                    </div>
                </div>
            </div>

            <div class="compare-footer">
                <div class="footer-left">
                    <span class="selected-count">
                        <i class="fa fa-check-circle"></i>
                        <strong id="selected-count-num">0</strong> products selected
                    </span>
                </div>
                <div class="footer-actions">
                    <button class="pxm-btn pxm-btn-clear" id="clear-selection-btn" style="display:none;">
                        <i class="fa fa-times-circle"></i>
                        Clear Selection
                    </button>
                    <button class="pxm-btn pxm-btn-primary" id="select-fields-btn" style="display:none;">
                        <i class="fa fa-filter"></i>
                        Select Fields
                    </button>
                </div>
            </div>
        `;
    },

    _attachCompareModalEvents(overlay, products) {
        const selectedProducts = new Set();
        const checkboxes = overlay.querySelectorAll('.product-checkbox');
        const cards = overlay.querySelectorAll('.product-card');
        const countSpan = overlay.querySelector('#selected-count-num');
        const table = overlay.querySelector('#comparison-table');
        const tableContainer = overlay.querySelector('#comparison-table-container');
        const placeholder = overlay.querySelector('#comparison-placeholder');
        const alertBox = overlay.querySelector('#compare-alert');
        const searchInput = overlay.querySelector('#product-search-input');
        const searchCount = overlay.querySelector('#search-results-count');
        const gridWrapper = overlay.querySelector('#product-grid-wrapper');
        const clearBtn = overlay.querySelector('#clear-selection-btn');
        const selectFieldsBtn = overlay.querySelector('#select-fields-btn');

        // Update comparison display
        const updateComparison = () => {
            const selected = products.filter(p => selectedProducts.has(p.id));

            if (selected.length >= 2) {
                placeholder.style.display = 'none';
                tableContainer.style.display = 'block';
                this._showComparisonTable(table, selected);

                if (selected.length === 2) {
                    setTimeout(() => {
                        tableContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 300);
                }
            } else {
                tableContainer.style.display = 'none';
                placeholder.style.display = 'flex';
            }
        };

        // Toggle buttons visibility
        const updateButtonsVisibility = () => {
            const count = selectedProducts.size;
            clearBtn.style.display = count > 0 ? 'inline-flex' : 'none';
            selectFieldsBtn.style.display = count >= 2 ? 'inline-flex' : 'none';
        };

        // Search functionality
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            let visibleCount = 0;

            cards.forEach(card => {
                const productName = card.dataset.productName;
                if (!query || productName.includes(query)) {
                    card.style.display = '';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            const grid = overlay.querySelector('#product-grid');
            const noResultsMsg = overlay.querySelector('.no-results-message');

            if (query) {
                searchCount.textContent = `${visibleCount} result${visibleCount !== 1 ? 's' : ''}`;
                searchCount.style.display = 'inline-block';
            } else {
                searchCount.style.display = 'none';
            }

            if (visibleCount === 0) {
                grid.style.display = 'none';
                noResultsMsg.style.display = 'flex';
                noResultsMsg.querySelector('p').textContent = `No products found matching "${query}"`;
            } else {
                grid.style.display = 'grid';
                noResultsMsg.style.display = 'none';
            }
        });

        // Checkbox change handler
        checkboxes.forEach(cb => {
            cb.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.productId);
                const card = overlay.querySelector(`.product-card[data-product-id="${id}"]`);

                if (e.target.checked) {
                    if (selectedProducts.size >= 4) {
                        e.target.checked = false;
                        alertBox.style.display = 'flex';
                        setTimeout(() => { alertBox.style.display = 'none'; }, 4000);
                        return;
                    }
                    selectedProducts.add(id);
                    card.classList.add('selected');
                } else {
                    selectedProducts.delete(id);
                    card.classList.remove('selected');
                    alertBox.style.display = 'none';
                }

                countSpan.textContent = selectedProducts.size;
                updateButtonsVisibility();
                updateComparison();
            });
        });

        // Card click handler
        cards.forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.classList.contains('product-checkbox') ||
                    e.target.classList.contains('checkbox-label')) return;

                const cb = card.querySelector('.product-checkbox');
                cb.checked = !cb.checked;
                cb.dispatchEvent(new Event('change'));
            });
        });

        // Clear selection
        clearBtn.addEventListener('click', () => {
            selectedProducts.clear();
            checkboxes.forEach(cb => {
                cb.checked = false;
                const card = overlay.querySelector(`.product-card[data-product-id="${cb.dataset.productId}"]`);
                if (card) card.classList.remove('selected');
            });
            countSpan.textContent = '0';
            updateButtonsVisibility();
            updateComparison();
        });

        // Select fields button
        selectFieldsBtn.addEventListener('click', () => {
            this._showFieldSelector(products, selectedProducts, table);
        });

        // Close handlers
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') overlay.remove();
        });
    },

    _showFieldSelector(products, selectedProducts, table) {
        const selected = products.filter(p => selectedProducts.has(p.id));
        const allKeys = new Set();
        selected.forEach(p => Object.keys(p.specs).forEach(k => allKeys.add(k)));

        const overlay = document.createElement('div');
        overlay.className = 'pxm-overlay pxm-field-overlay';

        const popup = document.createElement('div');
        popup.className = 'pxm-field-popup';

        const fieldsArray = Array.from(allKeys).sort();

        let html = `
            <div class="pxm-popup-header">
                <div class="pxm-popup-title">Select Fields to Compare</div>
                <div class="pxm-popup-subtitle">Choose which fields you want to include in the comparison</div>
            </div>

            <div class="pxm-search-container">
                <div class="pxm-search-box">
                    <span class="pxm-search-icon"><i class="fa fa-search"></i></span>
                    <input type="text" class="pxm-search-input" placeholder="Search fields..." id="field-search">
                </div>
            </div>

            <div class="pxm-action-bar">
                <span class="pxm-selected-count" id="selected-count">${fieldsArray.length} fields selected</span>
                <div class="pxm-quick-actions">
                    <button class="pxm-quick-btn" id="select-all">Select All</button>
                    <button class="pxm-quick-btn" id="deselect-all">Clear All</button>
                </div>
            </div>

            <div class="pxm-fields-container">`;

        fieldsArray.forEach(field => {
            html += `
                <div class="pxm-field-item">
                    <div class="pxm-checkbox-wrapper">
                        <input type="checkbox" class="pxm-checkbox field-checkbox" value="${field}" checked id="field-${field.replace(/\s/g, '-')}">
                    </div>
                    <label for="field-${field.replace(/\s/g, '-')}" class="pxm-field-label">${field}</label>
                </div>`;
        });

        html += `
            </div>

            <div class="pxm-popup-footer">
                <button class="pxm-btn pxm-btn-secondary" id="cancel-fields-btn">Cancel</button>
                <button class="pxm-btn pxm-btn-primary" id="apply-fields-btn">Apply Selection</button>
            </div>
        `;

        popup.innerHTML = html;
        overlay.appendChild(popup);
        document.body.appendChild(overlay);

        // Field selector events
        const searchInput = popup.querySelector('#field-search');
        const selectAllBtn = popup.querySelector('#select-all');
        const deselectAllBtn = popup.querySelector('#deselect-all');
        const cancelBtn = popup.querySelector('#cancel-fields-btn');
        const applyBtn = popup.querySelector('#apply-fields-btn');
        const checkboxes = popup.querySelectorAll('.field-checkbox');
        const selectedCountSpan = popup.querySelector('#selected-count');
        const fieldsContainer = popup.querySelector('.pxm-fields-container');

        const updateSelectedCount = () => {
            const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
            selectedCountSpan.textContent = `${checkedCount} field${checkedCount !== 1 ? 's' : ''} selected`;
        };

        // Search fields
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const fieldItems = fieldsContainer.querySelectorAll('.pxm-field-item');
            let visibleCount = 0;

            fieldItems.forEach(item => {
                const label = item.querySelector('.pxm-field-label').textContent.toLowerCase();
                if (label.includes(searchTerm)) {
                    item.style.display = '';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });

            const existingEmpty = fieldsContainer.querySelector('.pxm-empty-state');
            if (existingEmpty) existingEmpty.remove();

            if (visibleCount === 0) {
                const emptyState = document.createElement('div');
                emptyState.className = 'pxm-empty-state';
                emptyState.innerHTML = `
                    <div class="pxm-empty-icon">🔍</div>
                    <div class="pxm-empty-text">No fields found matching "${searchTerm}"</div>
                `;
                fieldsContainer.appendChild(emptyState);
            }
        });

        // Select/Deselect all
        selectAllBtn.addEventListener('click', () => {
            const visibleCheckboxes = Array.from(checkboxes).filter(cb =>
                cb.closest('.pxm-field-item').style.display !== 'none'
            );
            visibleCheckboxes.forEach(cb => cb.checked = true);
            updateSelectedCount();
        });

        deselectAllBtn.addEventListener('click', () => {
            const visibleCheckboxes = Array.from(checkboxes).filter(cb =>
                cb.closest('.pxm-field-item').style.display !== 'none'
            );
            visibleCheckboxes.forEach(cb => cb.checked = false);
            updateSelectedCount();
        });

        checkboxes.forEach(cb => {
            cb.addEventListener('change', updateSelectedCount);
        });

        // Field item click
        popup.querySelectorAll('.pxm-field-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'LABEL') {
                    const checkbox = item.querySelector('.pxm-checkbox');
                    checkbox.checked = !checkbox.checked;
                    updateSelectedCount();
                }
            });
        });

        // Cancel
        cancelBtn.addEventListener('click', () => overlay.remove());

        // Apply
        applyBtn.addEventListener('click', () => {
            const checkedFields = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);

            if (checkedFields.length === 0) {
                this._showNotification('Please select at least one field', 'warning');
                return;
            }

            this._showComparisonTable(table, selected, checkedFields);
            overlay.remove();
        });

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });

        // Close on Escape
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                overlay.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    },

    _showComparisonTable(table, products, fieldsFilter = null) {
        if (products.length < 2) return;

        let allKeys = new Set();
        products.forEach(p => Object.keys(p.specs).forEach(k => allKeys.add(k)));

        if (fieldsFilter && fieldsFilter.length > 0) {
            allKeys = new Set(fieldsFilter);
        }

        const sortedKeys = Array.from(allKeys).sort();

        let html = `
            <thead>
                <tr>
                    <th class="field-column">Product Details</th>
                    ${products.map(p => `
                        <th class="product-column">
                            <div class="product-header-content">
                                <img src="${p.image}" alt="${p.name}" onerror="this.src='/images/NoImage.jpg'">
                                <div class="product-header-info">
                                    <div class="product-header-name">${p.name}</div>
                                </div>
                            </div>
                        </th>
                    `).join('')}
                </tr>
            </thead>
            <tbody>
                ${sortedKeys.map((key, index) => `
                    <tr class="${index % 2 === 0 ? 'even-row' : 'odd-row'}">
                        <td class="field-name">${key}</td>
                        ${products.map(p => {
                            const value = p.specs[key] || 'N/A';
                            return `<td class="field-value">${value}</td>`;
                        }).join('')}
                    </tr>
                `).join('')}
            </tbody>
        `;

        table.innerHTML = html;
        table.classList.add('active');
    },

    _showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `pxm-notification pxm-notification-${type}`;
        notification.innerHTML = `
            <i class="fa fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    // ========================================
    // GALLERY INITIALIZATION
    // ========================================
    _initGallery() {
        const mainImg = this.el.querySelector("#mainProductImage");
        const thumbs = Array.from(this.el.querySelectorAll(".thumb-item"));
        if (!mainImg || !thumbs.length) return;

        let currentIndex = 0;

        const updateImage = (index) => {
            const newSrc = thumbs[index].dataset.src || thumbs[index].src;
            mainImg.src = newSrc;

            thumbs.forEach(t => t.classList.remove("border-primary"));
            thumbs[index].classList.add("border-primary");

            const thumbEl = thumbs[index];
            const carousel = this.el.querySelector(".thumbnail-carousel");
            if (carousel) {
                carousel.scrollTo({
                    left: thumbEl.offsetLeft - (carousel.clientWidth / 2) + (thumbEl.offsetWidth / 2),
                    behavior: "smooth"
                });
            }
        };

        thumbs.forEach((thumb, i) => {
            thumb.addEventListener("click", () => {
                currentIndex = i;
                updateImage(i);
            });
        });

        this.el.querySelector(".left-arrow")?.addEventListener("click", () => {
            currentIndex = (currentIndex - 1 + thumbs.length) % thumbs.length;
            updateImage(currentIndex);
        });

        this.el.querySelector(".right-arrow")?.addEventListener("click", () => {
            currentIndex = (currentIndex + 1) % thumbs.length;
            updateImage(currentIndex);
        });

        updateImage(0);
    },
});














