/** @odoo-module */
import { Component, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class Filters extends Component {
    static template = "odoopim_split_widget.Filters";
    static props = {
        searchModel: { type: Object },
        onClose: { type: Function },
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.actionService = useService("action");

        this.saveInput = useRef("saveInput");
        this.renameInput = useRef("renameInput");
        // Track all item IDs before we start adding filters
        this.initialItemIds = new Set(
            Object.keys(this.props.searchModel.searchItems || {}).map(id => parseInt(id))
        );

        this.state = useState({
            selectedFilters: {},
            savedFilters: [],
            allFamilies: [],
            selectedFilterId: null,
            filterToRename: null,
            isEditing: false,
            selectedFamilyId: null,
            commonFilters: [
                {
                    group_name: "Status",
                    filters: [
                        {
                            label: "All",
                            domain: '["|",("active","=",True),("active","=",False)]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Enable",
                            domain: '[("active","=",True)]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Disable",
                            domain: '[("active","=",False)]',
                            action: this._onSelect.bind(this),
                        },
                    ],
                },
                {
                    group_name: "Complete",
                    filters: [
                        {
                            label: "Fully Completed",
                            domain: '[("percentage_complete","=",100)]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Almost Completed",
                            domain: '["&",("percentage_complete",">=",80),("percentage_complete","<",100)]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Partially Completed",
                            domain: '["&",("percentage_complete",">=",50),("percentage_complete","<",80)]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Incomplete",
                            domain: '["&",("percentage_complete",">=",30),("percentage_complete","<",50)]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Not Completed",
                            domain: '[("percentage_complete","<",30)]',
                            action: this._onSelect.bind(this),
                        },
                    ],
                },
                {
                    group_name: "Product Type",
                    filters: [
                        {
                            label: "Service",
                            domain: '[("type","=","service")]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Goods",
                            domain: '[("type","=","consu")]',
                            action: this._onSelect.bind(this),
                        },
                        {
                            label: "Combo",
                            domain: '[("type","=","combo")]',
                            action: this._onSelect.bind(this),
                        },
                    ],
                },
            ],
        });

        this.getData();
        this.prepareDynamicFilters();
        this.loadSavedFilters();
    }

    /* --------------------------------------------------------------------- *
     *  Dynamic filters (Categories / Brands)
     * --------------------------------------------------------------------- */
    async getAlCategories() {
        try {
            const activeCompanyIds = this.env.services.company.activeCompanyIds;
            return await this.orm.searchRead("pim.category", [['company_id', 'in', activeCompanyIds]], ["id", "name"]);
        } catch {
            return [];
        }
    }

    async getProductBrands() {
        try {
            const activeCompanyIds = this.env.services.company.activeCompanyIds;
            return await this.orm.searchRead("product.brand", [['company_id', 'in', activeCompanyIds]], ["id", "name"]);
        } catch {
            return [];
        }
    }

    async prepareDynamicFilters() {
        const [categories, brands] = await Promise.all([this.getAlCategories(), this.getProductBrands()]);

        if (categories?.length) {
            const cat = { group_name: "Categories", filters: [] };
            for (const c of categories) {
                cat.filters.push({
                    label: c.name,
                    domain: `[("pim_category_ids","in",[${c.id}])]`,
                    action: this._onSelect.bind(this),
                });
            }
            this.state.commonFilters.push(cat);
        }

        if (brands?.length) {
            const br = { group_name: "Brands", filters: [] };
            for (const b of brands) {
                br.filters.push({
                    label: b.name,
                    domain: `[("brand_id","=",${b.id})]`,
                    action: this._onSelect.bind(this),
                });
            }
            this.state.commonFilters.push(br);
        }
    }

    /* --------------------------------------------------------------------- *
     *  Family filter (select box)
     * --------------------------------------------------------------------- */
    async getData() {
        try {
            const activeCompanyIds = this.env.services.company.activeCompanyIds;
            const allFamilies = await this.orm.searchRead(
                "family.attribute",
                [['company_id', 'in', activeCompanyIds]],
                ["id", "name"]
            );
            this.state.allFamilies = allFamilies || [];
        } catch {
            this.state.allFamilies = [];
        }
    }

    async onFamilyChange(ev) {
        const familyId = parseInt(ev.target.value, 10);
        this.state.selectedFamilyId = familyId;
        const label = ev.target.options[ev.target.selectedIndex].text;
        const group_name = "Family";

        this._removeGroup(group_name);

        if (!familyId) {
            return;
        }

        const beforeIds = this._getCurrentItemIds();
        const domain = `[("family_id","=",${familyId})]`;
        await this.props.searchModel.splitAndAddDomain(domain);

        const afterIds = this._getCurrentItemIds();
        const newItemIds = afterIds.filter(id => !beforeIds.includes(id));
        this.state.selectedFilters[group_name] = { label, itemIds: newItemIds };
    }

    /* --------------------------------------------------------------------- *
     *  Click on any filter button (Complete, Status, …)
     * --------------------------------------------------------------------- */
    async _onSelect(ev) {
        const domain = ev.target.dataset.domain;
        const group_name = ev.target.dataset.group;
        const label = ev.target.innerText.trim();

        if (this.state.selectedFilters[group_name]?.label === label) {
            this._removeGroup(group_name);
            return;
        }

        if (this.state.selectedFilters[group_name]) {
            this._removeGroup(group_name);
        }

        const beforeIds = this._getCurrentItemIds();
        await this.props.searchModel.splitAndAddDomain(domain);

        const afterIds = this._getCurrentItemIds();
        const newItemIds = afterIds.filter(id => !beforeIds.includes(id));
        this.state.selectedFilters[group_name] = { label, itemIds: newItemIds };
    }

    /* --------------------------------------------------------------------- *
     *  Helper – Get current item IDs from search model
     * --------------------------------------------------------------------- */
    _getCurrentItemIds() {
        const searchItems = this.props.searchModel.searchItems || {};
        return Object.keys(searchItems).map(id => parseInt(id)).sort((a, b) => a - b);
    }

    /* --------------------------------------------------------------------- *
     *  Helper – remove EVERYTHING that belongs to a group
     * --------------------------------------------------------------------- */
    _removeGroup(group_name) {
        const filterData = this.state.selectedFilters[group_name];
        if (!filterData) {
            return;
        }

        if (!filterData.itemIds || filterData.itemIds.length === 0) {
            delete this.state.selectedFilters[group_name];
            return;
        }

        for (const itemId of filterData.itemIds) {
            const item = this.props.searchModel.searchItems[itemId];
            if (!item) {
                continue;
            }
            try {
                this.props.searchModel.toggleSearchItem(itemId);
            } catch { }
        }

        delete this.state.selectedFilters[group_name];
    }

    /* --------------------------------------------------------------------- *
     *  Misc helpers (used by the XML)
     * --------------------------------------------------------------------- */
    clearAllFilters() {
        const groupNames = Object.keys(this.state.selectedFilters);
        for (const group_name of groupNames) {
            this._removeGroup(group_name);
        }
        this.state.selectedFilters = {};
        this.state.selectedFamilyId = null;
    }

    removeFilter(group_name) {
        this._removeGroup(group_name);
    }

    close() {
        this.state.selectedFamilyId = null
        this.props.onClose();
    }

    /* --------------------------------------------------------------------- */

    async getUserId() {
        try {
            const userInfo = await this.orm.call("res.users", "context_get", [], {});
            return userInfo.uid || false;
        } catch (e) {
            console.error('Error occurred to find user', e);
            return false;
        }
    }
    async loadSavedFilters() {
        try {
            const model = "product.template";
            const userId = await this.getUserId();
            const domain = [
                ["model_id", "=", model],
                "|",
                    ["user_id", "=", userId],
                    ["shared_user_ids", "in", [userId]]
            ];

            // IMPORTANT: We need the 'domain' field to apply the filter later
            const filters = await this.orm.searchRead(
                "ir.filters",
                domain,
                ["id", "name", "domain", "is_default", "user_id", "shared_user_ids"]
            );

            this.state.savedFilters = filters.sort((a, b) => a.name.localeCompare(b.name));
        } catch (err) {
            console.error("Failed to load saved filters", err);
            this.state.savedFilters = [];
        }
    }

    async onSavedChange(filterId) {
        if (this.state.isEditing) return;
        if (isNaN(filterId)) return;

        const savedFilter = this.state.savedFilters.find(f => f.id === filterId);
        if (!savedFilter) return;

        try {
            this.clearAllFilters();

            // Parse the saved domain
            let domain = [];
            try {
                domain = JSON.parse(savedFilter.domain || "[]");
            } catch (e) {
                console.error("Invalid domain in saved filter", savedFilter.id, e);
                this.notification.add("Invalid saved filter domain.", { type: "danger" });
                return;
            }

            // update domain
            if (typeof this.props.searchModel.reset === "function") {
                await this.props.searchModel.reset({ domain });
            } else if (typeof this.props.searchModel.setDomain === "function") {
                await this.props.searchModel.setDomain(domain);
            } else {
                if (typeof this.props.searchModel.clearQuery === "function") {
                    await this.props.searchModel.clearQuery();
                }
                await this.props.searchModel.splitAndAddDomain(domain, { replace: true });
            }
            this.state.selectedFilterId = filterId;
            this.notification.add("Saved filter applied successfully.", { type: "success" });
        } catch (err) {
            console.error("Failed to apply saved filter", err);
            this.notification.add("Failed to apply the saved filter.", { type: "danger" });
        }
    }

    async saveCurrent() {
        const name = this.saveInput.el?.value.trim();
        if (!name) {
            this.notification.add("Please enter a name for the filter.", { type: "warning" });
            return;
        }
        if (Object.keys(this.state.selectedFilters).length === 0) {
            this.notification.add("No filters are currently applied.", { type: "warning" });
            return;
        }

        try {
            const model = "product.template";
            const currentDomain = this.props.searchModel.domain || [];
            const userId = await this.getUserId();

            await this.orm.create("ir.filters", [{
                name: name,
                model_id: model,
                domain: JSON.stringify(currentDomain),
                context: JSON.stringify({}),
                sort: JSON.stringify([]),
                user_id: userId,
            }]);

            this.notification.add(`Filter "${name}" saved successfully!`, { type: "success" });
            this.saveInput.el.value = "";
            await this.loadSavedFilters();

        } catch (err) {
            console.error("Failed to save filter", err);
            this.notification.add("Could not save the filter.", { type: "danger" });
        }
    }

    clearSavedDomain = async () => {
        await this.props.searchModel.clearQuery();
        this.state.selectedFilterId = null;
    }

    // Set as default
    async toggleDefault(filterId) {
        const filter = this.state.savedFilters.find(f => f.id === filterId);
        if (!filter) return;

        try {
            // First, unset any existing default for this model/user
            const existingDefaults = this.state.savedFilters.filter(f => f.is_default);
            if (existingDefaults.length > 0) {
                await this.orm.write("ir.filters", existingDefaults.map(f => f.id), { is_default: false });
            }

            // Set the new one (or unset if it was already default)
            await this.orm.write("ir.filters", [filterId], { is_default: !filter.is_default });

            await this.loadSavedFilters();

            this.notification.add(
                filter.is_default
                    ? `Filter "${filter.name}" is no longer default.`
                    : `Filter "${filter.name}" set as default!`,
                { type: "success" }
            );
        } catch (err) {
            console.error("Failed to toggle default filter", err);
            this.notification.add("Could not update default filter.", { type: "danger" });
        }
    }

    startRename(saved) {
        this.state.filterToRename = { id: saved.id, name: saved.name };
        this.state.isEditing = true;
        // Focus and select after next render
        setTimeout(() => {
            const input = this.__owl__.refs.renameInput;
            if (input) {
                input.focus();
                input.select();
            }
        }, 0);
    }

    async renameFilter(filterId, newName) {
        newName = newName.trim();
        if (!newName) {
            this.notification.add("Filter name cannot be empty.", { type: "warning" });
            this.state.filterToRename = null;
            return;
        }

        const oldFilter = this.state.savedFilters.find(f => f.id === filterId);
        if (newName === oldFilter.name) {
            this.state.filterToRename = null;
            this.state.isEditing = false;
            return;
        }

        try {
            await this.orm.write("ir.filters", [filterId], { name: newName });
            this.notification.add("Filter renamed successfully.", { type: "success" });
            this.state.isEditing = false;
            await this.loadSavedFilters();
        } catch (err) {
            console.error("Failed to rename filter", err);
            this.notification.add("Could not rename filter.", { type: "danger" });
        } finally {
            this.state.filterToRename = null;
        }
    }

    cancelRenameFilter = () => {
        this.state.filterToRename = null;
        this.state.isEditing = false;
        return;
    }

    async openShareDialog(filterId) {
        const filter = this.state.savedFilters.find(f => f.id === filterId);
        if (!filter) return;

        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "ir.filters",
            res_id: filterId,
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            name: `Share Filter: ${filter.name}`,
            context: {
                form_view_ref: "odoopim_split_widget.view_ir_filters_share_dialog_form",
            },
            flags: {
                mode: "edit",
            },
        });
    }


    // Delete
    deleteFilter = async (filterId) => {
        this.dialog.add(ConfirmationDialog, {
            title: "Delete Saved Filter",
            body: "Are you sure you want to delete this saved filter?",
            confirmLabel: "Delete",
            confirmClass: "btn-danger",
            cancelLabel: "Cancel",
            confirm: async () => {
                try {
                    await this.orm.unlink("ir.filters", [filterId]);
                    this.notification.add("Filter deleted.", { type: "success" });
                    await this.loadSavedFilters();
                } catch (err) {
                    console.error(err);
                    this.notification.add("Could not delete filter.", { type: "danger" });
                }
            },
        });
    };
}