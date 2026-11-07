/** @odoo-module **/
import {registry} from "@web/core/registry";
import {Component, useState, onWillStart, onWillUpdateProps} from "@odoo/owl";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";
import {rpc} from "@web/core/network/rpc";

const ODOO_COLORS = [
    null,        // 0: No color
    '#ef5350',   // 1: Red
    '#ffa726',   // 2: Orange
    '#ffeb3b',   // 3: Yellow
    '#26c6da',   // 4: Cyan
    '#7e57c2',   // 5: Purple
    '#d7ccc8',   // 6: Almond
    '#00897b',   // 7: Teal
    '#1976d2',   // 8: Blue
    '#d81b60',   // 9: Raspberry
    '#388e3c',   // 10: Green
    '#8e24aa',   // 11: Violet
];

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : null;
}

export class PimAssociationManager extends Component {
    static template = "odoo_pim_association.AssociationManager";
    static props = {...standardFieldProps};
    static ODOO_COLORS = ODOO_COLORS;

    setup() {
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.state = useState({
            types: [],
            selectedType: null,
            loading: true,
            productId: null,
            companyId: null,
            associatedProducts: [],
            dropdownOpen: false
        });

        onWillStart(async () => {
            await this.loadData();
        });

        // Handle record changes in split view
        onWillUpdateProps(async (nextProps) => {
            const currentProductId = this.props.record.resId;
            const nextProductId = nextProps.record.resId;

            // Reload if product changed
            if (currentProductId !== nextProductId) {
                this.state.loading = true;
                // Keep the same selected type if possible
                await this.loadDataForNewRecord(nextProps, true);
                this.state.loading = false;
            }
        });
    }

    async loadData(keepSelectedType = false) {
        try {
            this.state.productId = this.props.record.resId;
            this.state.companyId = this.props.record.data.company_id
                ? (Array.isArray(this.props.record.data.company_id)
                    ? this.props.record.data.company_id[0]
                    : this.props.record.data.company_id)
                : null;

            const previousSelectedType = this.state.selectedType;

            // Load types with counts
            const result = await rpc("/pim/association/get_types", {
                company_id: this.state.companyId,
                product_id: this.state.productId
            });

            if (result.success) {
                this.state.types = result.types;

                if (keepSelectedType && previousSelectedType) {
                    // Keep previous selection if it still exists
                    const typeExists = result.types.find(t => t.id === previousSelectedType);
                    if (typeExists) {
                        this.state.selectedType = previousSelectedType;
                    } else if (result.types.length > 0) {
                        this.state.selectedType = result.types[0].id;
                    }
                } else if (result.types.length > 0 && !this.state.selectedType) {
                    this.state.selectedType = result.types[0].id;
                }

                // Load associated products for selected type
                await this.loadAssociatedProducts();
            }

            this.state.loading = false;
        } catch (error) {
            const message =
                error?.data?.message ||
                error?.data?.arguments?.[0] ||
                "Error loading data. Please try again.";

            this.notification.add(message, {
                type: "danger",
            });

            this.state.loading = false;
        }
    }

    async loadDataForNewRecord(props, keepSelectedType = false) {
        try {
            this.state.productId = props.record.resId;
            this.state.companyId = props.record.data.company_id
                ? (Array.isArray(props.record.data.company_id)
                    ? props.record.data.company_id[0]
                    : props.record.data.company_id)
                : null;

            const previousSelectedType = this.state.selectedType;

            // Load types with new counts
            const result = await rpc("/pim/association/get_types", {
                company_id: this.state.companyId,
                product_id: this.state.productId
            });

            if (result.success) {
                this.state.types = result.types;

                if (keepSelectedType && previousSelectedType) {
                    const typeExists = result.types.find(t => t.id === previousSelectedType);
                    if (typeExists) {
                        this.state.selectedType = previousSelectedType;
                    } else if (result.types.length > 0) {
                        this.state.selectedType = result.types[0].id;
                    }
                } else if (result.types.length > 0) {
                    this.state.selectedType = result.types[0].id;
                }

                // Load products for the selected type
                await this.loadAssociatedProducts();
            }
        } catch (error) {
            this.notification.add(
                `Error loading data for new record: ${error?.data?.message || error?.message || ""}`,
                {type: "danger"}
            );
        }

    }

    async loadAssociatedProducts() {
        if (!this.state.selectedType || !this.state.productId) {
            this.state.associatedProducts = [];
            return;
        }

        try {
            const result = await rpc("/pim/association/get_associated_products", {
                product_id: this.state.productId,
                association_type_id: this.state.selectedType
            });

            if (result.success) {
                this.state.associatedProducts = result.products;
            } else {
                this.state.associatedProducts = [];
            }
        } catch (error) {
            const message =
                error?.message ||
                error?.data?.message ||
                "Error loading associated products.";

            this.notification.add(message, {
                type: "danger",
                sticky: false,
            });

            this.state.associatedProducts = [];
        }
    }

    onTypeClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const typeId = parseInt(ev.currentTarget.dataset.typeId, 10);
        this.selectType(typeId);
        this.closeDropdown();
    }

    async selectType(typeId) {
        this.state.selectedType = typeId;
        await this.loadAssociatedProducts();
    }

    toggleDropdown() {
        this.state.dropdownOpen = !this.state.dropdownOpen;
    }

    closeDropdown() {
        this.state.dropdownOpen = false;
    }

    getSelectedTypeName() {
        const type = this.state.types.find(t => t.id === this.state.selectedType);
        return type ? type.name : 'Select Type';
    }

    getSelectedTypeCount() {
        const type = this.state.types.find(t => t.id === this.state.selectedType);
        return type ? type.count : 0;
    }

    getCount(typeId) {
        const type = this.state.types.find(t => t.id === typeId);
        return type ? type.count : 0;
    }

    getTypeColor(colorIndex) {
        return this.constructor.ODOO_COLORS[colorIndex] || '';
    }

    getTypeBgColor(colorIndex) {
        const color = this.getTypeColor(colorIndex);
        if (!color) return '';
        const rgb = hexToRgb(color);
        if (!rgb) return '';
        return `rgba(${rgb}, 0.1)`;
    }

    getSelectedTypeColor() {
        const type = this.state.types.find(t => t.id === this.state.selectedType);
        return type ? this.getTypeColor(type.color) : '';
    }

    getSelectedTypeBgColor() {
        const type = this.state.types.find(t => t.id === this.state.selectedType);
        return type ? this.getTypeBgColor(type.color) : '';
    }

    async openDialog() {
        if (!this.state.selectedType) {
            this.notification.add("Please select an association type", {
                type: "warning",
                title: "Warning"
            });
            return;
        }

        this.dialog.add(AssociationDialog, {
            productId: this.state.productId,
            companyId: this.state.companyId,
            associationTypeId: this.state.selectedType,
            onSave: async () => {
                // Reload types and products with updated counts
                await this.loadData(true);

                this.notification.add("Products added successfully!", {
                    type: "success",
                    title: "Success"
                });
            }
        });
    }

    getImageUrl(product) {
        if (product.image_128) {
            return `data:image/png;base64,${product.image_128}`;
        }
        return "/web/static/img/placeholder.png";
    }

    getProgressBarColor(percentage) {
        if (percentage >= 80) return "#10B981";
        if (percentage >= 60) return "#3B82F6";
        if (percentage >= 40) return "#F59E0B";
        return "#EF4444";
    }

    removeProduct(ev) {
        const productId = parseInt(ev.currentTarget.dataset.productId, 10);
        const product = this.state.associatedProducts.find(p => p.id === productId);

        this.dialog.add(DeleteConfirmationDialog, {
            product: product,
            onConfirm: async () => {
                const filtered = this.state.associatedProducts.filter(p => p.id !== productId);
                const productIds = filtered.map(p => p.id);

                const result = await rpc("/pim/association/save_associations", {
                    source_product_id: this.state.productId,
                    associated_product_ids: productIds,
                    association_type_id: this.state.selectedType
                });

                if (result.success) {
                    // Reload data to update counts and products
                    await this.loadData(true);

                    this.notification.add("Product removed successfully!", {
                        type: "success",
                        title: "Success"
                    });
                }
            }
        });
    }
}

// DELETE CONFIRMATION DIALOG
export class DeleteConfirmationDialog extends Component {
    static template = "odoo_pim_association.DeleteConfirmationDialog";
    static props = {
        close: Function,
        product: Object,
        onConfirm: Function
    };

    getImageUrl(product) {
        if (product.image_128) {
            return `data:image/png;base64,${product.image_128}`;
        }
        return "/web/static/img/placeholder.png";
    }

    async onConfirm() {
        await this.props.onConfirm();
        this.props.close();
    }

    onClose() {
        this.props.close();
    }
}

// ASSOCIATION DIALOG
export class AssociationDialog extends Component {
    static template = "odoo_pim_association.AssociationDialog";
    static props = {
        close: Function,
        productId: Number,
        companyId: [Number, {value: null}],
        associationTypeId: Number,
        onSave: {type: Function, optional: true}
    };

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            products: [],
            filteredProducts: [],
            selectedProducts: [],
            categories: [],
            families: [],
            filters: {
                category_id: false,
                family_id: false,
                active: true
            },
            searchQuery: "",
            loading: true,
            error: null
        });

        onWillStart(async () => {
            await this.loadData();
            this.applyFilters();
        });
    }

    async loadData() {
        try {
            const result = await rpc("/pim/association/get_products", {
                current_product_id: this.props.productId,
                association_type_id: this.props.associationTypeId,
                company_id: this.props.companyId
            });

            if (result.success) {
                this.state.products = result.products;
                this.state.filteredProducts = result.products;
                this.state.categories = result.categories;
                this.state.families = result.families;
                this.state.selectedProducts = [...result.existing_associations];
            } else {
                this.state.error = result.error || "Failed to load products";
            }

            this.state.loading = false;
        } catch (error) {
            this.state.error = "Network error: " + error.message;
            this.state.loading = false;
        }
    }

    applyFilters() {
        let filtered = [...this.state.products];

        if (this.state.filters.category_id) {
            filtered = filtered.filter(p =>
                p.pim_category_ids && p.pim_category_ids.includes(this.state.filters.category_id)
            );
        }

        if (this.state.filters.family_id) {
            filtered = filtered.filter(p =>
                p.family_id && p.family_id[0] === this.state.filters.family_id
            );
        }

        if (this.state.filters.active !== null) {
            filtered = filtered.filter(p => p.active === this.state.filters.active);
        }

        if (this.state.searchQuery) {
            const query = this.state.searchQuery.toLowerCase();
            filtered = filtered.filter(p => {
                const name = (p.name || "").toLowerCase();
                const sku = (p.sku || "").toLowerCase();
                const family = p.family_id ? p.family_id[1].toLowerCase() : "";
                return name.includes(query) || sku.includes(query) || family.includes(query);
            });
        }

        this.state.filteredProducts = filtered;
    }

    onCategoryChange(ev) {
        this.state.filters.category_id = parseInt(ev.target.value, 10) || false;
        this.applyFilters();
    }

    onFamilyChange(ev) {
        this.state.filters.family_id = parseInt(ev.target.value, 10) || false;
        this.applyFilters();
    }

    onStatusChange(ev) {
        const value = ev.target.value;
        this.state.filters.active = value === "active" ? true : value === "inactive" ? false : null;
        this.applyFilters();
    }

    onSearchChange(ev) {
        this.state.searchQuery = ev.target.value;
        this.applyFilters();
    }

    resetFilters() {
        this.state.filters = {
            category_id: false,
            family_id: false,
            active: true
        };
        this.state.searchQuery = "";
        this.applyFilters();
    }

    getActiveFilterCount() {
        let count = 0;
        if (this.state.filters.category_id) count++;
        if (this.state.filters.family_id) count++;
        if (this.state.searchQuery) count++;
        return count;
    }

    onProductClick(ev) {
        const productId = parseInt(ev.currentTarget.dataset.productId, 10);
        this.onProductSelect(productId);
    }

    onSelectedProductClick(ev) {
        const productId = parseInt(ev.currentTarget.dataset.productId, 10);
        this.onProductSelect(productId);
    }

    onProductSelect(productId) {
        const index = this.state.selectedProducts.indexOf(productId);
        if (index > -1) {
            this.state.selectedProducts.splice(index, 1);
        } else {
            this.state.selectedProducts.push(productId);
        }
    }

    isProductSelected(productId) {
        return this.state.selectedProducts.includes(productId);
    }

    getSelectedProductsData() {
        return this.state.products.filter(p => this.state.selectedProducts.includes(p.id));
    }

    clearAllSelected() {
        this.state.selectedProducts = [];
    }

    getProgressBarColor(percentage) {
        if (percentage >= 80) return "#10B981";
        if (percentage >= 60) return "#3B82F6";
        if (percentage >= 40) return "#F59E0B";
        return "#EF4444";
    }

    getImageUrl(product) {
        if (product.image_1920) {
            return `data:image/png;base64,${product.image_1920}`;
        }
        return "/web/static/img/placeholder.png";
    }

    async onClose() {
        this.props.close();
    }

    async onSave() {
        try {
            const result = await rpc("/pim/association/save_associations", {
                source_product_id: this.props.productId,
                associated_product_ids: this.state.selectedProducts,
                association_type_id: this.props.associationTypeId
            });

            if (result.success) {
                if (this.props.onSave) {
                    await this.props.onSave();
                }
                await this.onClose();
            } else {
                this.notification.add("Error saving: " + result.error, {type: "danger"});
            }
        } catch (error) {
            this.notification.add("Error saving: " + error.message, {type: "danger"});
        }
    }
}

registry.category("fields").add("pim_association_manager", {
    component: PimAssociationManager
});