/** @odoo-module */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { session } from "@web/session";
import { user } from "@web/core/user";
import { TreeFormControllerBus } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";

export class EditCommonAttribute extends Component {
    static template = "odoopim_split_widget.EditCommonAttribute";
    static props = {
        renderer: { type: Object },
        controller: { type: Object },
        action: { type: Object },
    };

    async _read(model, domain = [], fields = []) {
        const res = await this.props.controller.orm.searchRead(model, domain, fields);
        if (Array.isArray(res)) return res;
        if (res && res.records) return res.records;
        if (res && res.data) return res.data;
        return [];
    }

    setup() {
        super.setup();

        this.state = useState({
            aiProviders: [],
            aiModels: [],
            aiFilteredModels: [],
            aiFields: [],
            promptTypes: [],
            productCount: 0,
            attributeValues: {},
            attributes: [],
            searchFieldText: "",
            filteredAiFields: [],
            showDropdown: false,
            isSearchFocused: false,   // <-- ADD THIS

        });

        this.onFieldCheckboxChange = (ev, id) => {
            const checked = ev.target.checked;
            if (!this.state.attributeValues.field_ids) {
                this.state.attributeValues.field_ids = [];
            }
            if (checked) {
                if (!this.state.attributeValues.field_ids.includes(id)) {
                    this.state.attributeValues.field_ids.push(id);
                }
            } else {
                this.state.attributeValues.field_ids =
                    this.state.attributeValues.field_ids.filter(x => x !== id);
            }

            // Reset search
            this.state.searchFieldText = "";
            this.state.filteredAiFields = [...this.state.aiFields];

            // ⭐ CLOSE DROPDOWN AFTER SELECTING FIELD
            this.state.showDropdown = false;
        };

        this.removeField = (id) => {
            this.state.attributeValues.field_ids =
                (this.state.attributeValues.field_ids || []).filter(x => x !== id);
        };

        // Load backend data
        if (this.props.action.action === "AI_ENRICHMENT") {
            this.loadAIData();
        }

        this.getData();

        // OUTSIDE CLICK LISTENER — 100% working in Odoo
        onMounted(() => {
            this._onClickOutside = this.onClickOutside.bind(this);
            document.addEventListener("pointerdown", this._onClickOutside, true);
        });

        onWillUnmount(() => {
            document.removeEventListener("pointerdown", this._onClickOutside, true);
        });
    }

    // Show dropdown when user focuses input
    onFocusShowDropdown() {
        this.state.showDropdown = true;
    }

    // MAIN OUTSIDE CLICK HANDLER ⭐⭐
    onClickOutside(ev) {
        const wrapper = this.refs?.dropdownWrapper;
        if (!wrapper) return;

        if (!wrapper.contains(ev.target)) {
            this.state.showDropdown = false;
        }
    }

    // Search handler
    onSearchField(ev) {
        const search = (ev.target.value || "").toLowerCase();
        this.state.filteredAiFields = this.state.aiFields.filter(f =>
            (f.name || "").toLowerCase().includes(search)
        );

        this.state.showDropdown = true;
    }

    // Clear (×) button handler
    clearSearch(ev) {
        ev.stopPropagation();
        ev.preventDefault();

        this.state.searchFieldText = "";
        this.state.filteredAiFields = [...this.state.aiFields];
        this.state.showDropdown = false;
        this.state.isSearchFocused = false;
    }


    onFocusSearch() {
        this.state.isSearchFocused = true;
        this.state.showDropdown = true;
    }

    onBlurSearch(ev) {
        // If the blur moved focus to the X button, do NOT hide the X
        if (ev.relatedTarget && ev.relatedTarget.classList.contains("clear-search-btn")) {
            return;
        }

        setTimeout(() => {
            this.state.isSearchFocused = false;
        }, 100);
    }

    async buildFinalPayload() {
        const selectedRecords = this.props.renderer.env.model.root.selection || [];

        const products = selectedRecords.map(rec => ({
            id: rec.data?.id || rec.resId || rec._values?.id,
            name: rec.data?.display_name || rec._values?.name || rec.name,
            sku: rec.data?.sku || false,
            list_price: rec.data?.list_price || 0,
            standard_price: rec.data?.standard_price || 0,
            hsn_code: rec.data?.hsn_code || false,
            tracking: rec.data?.tracking || "",
            supplier_taxes: rec.data?.supplier_taxes_id || [],
            sales_taxes: rec.data?.taxes_id || [],
            sale_ok: rec.data?.sale_ok ?? true,
            purchase_ok: rec.data?.purchase_ok ?? true,
        }));

        const aiConfig = this.state.aiModels.find(
            m => m.id === this.state.attributeValues.model_id
        );

        const ctx = {
            source: "odoo",
            odoo_url: window.location.origin,
            odoo_db: session.db,
            odoo_username: user.login,
            odoo_password: aiConfig?.password || "",
        };

        const ai = {
            provider: this.state.attributeValues.provider,
            model: aiConfig?.code || "",
            token: false,
            url: aiConfig?.api_url || "",
            key: aiConfig?.api_key || "",
        };

        const promptTypeObj = this.state.promptTypes.find(
            p => p.id == this.state.attributeValues.prompt_type
        );

        const updateFields = [];

        for (const id of this.state.attributeValues.field_ids || []) {
            const f = this.state.aiFields.find(x => x.id === id);
            if (!f) continue;

            let irFieldId = null;
            let techName = null;
            let label = null;
            let fieldModel = "product.template";


            if (f.source_model === "general.attribute") {
                const attrRecs = await this._read(
                    "general.attribute",
                    [["id", "=", f.source_id]],
                    ["name", "is_ai_enrichable"]
                );
                const attr = attrRecs?.[0];

                if (!attr || attr.is_ai_enrichable !== true) {
                    // Skip if not marked enrichable
                    continue;
                }

                const attrNameRaw = attr.name || "";
                // normalize to avoid ":" or case issues
                const normalized = attrNameRaw.toLowerCase().replace(/:/g, "").trim();

                // ✅ Map special general attributes to real product fields
                if (normalized === "product name") {
                    techName = "name";
                    label = "Product Name";
                    fieldModel = "product.template";
                } else if (
                    normalized === "product description" ||
                    normalized === "description"
                ) {
                    techName = "description";
                    label = "Product Description";
                    fieldModel = "product.template";
                } else {
                    // ✅ Custom general attribute → dynamic x_att field
                    // Try to find x_att<id>_* field
                    const searchPattern = `x_att${f.source_id}_%`;

                    const fields = await this._read(
                        "ir.model.fields",
                        [
                            ["model", "in", ["product.template", "product.product"]],
                            ["name", "=like", searchPattern],
                        ],
                        ["id", "name", "field_description", "model"]
                    );

                    if (fields.length > 0) {
                        techName = fields[0].name;                      // e.g. x_att906_electronics_demo
                        label = fields[0].field_description || f.name;  // e.g. "Screen Type"
                    } else {
                        // Fallback: send just the technical name from ai.enrichment.field
                        techName = f.name;
                        label = f.name;
                    }
                }
            }

            else if (f.source_model === "product.attribute") {
                const rec = await this._read(
                    "product.attribute",
                    [["id", "=", f.source_id]],
                    ["product_template_field_id", "name", "original_name"]
                );

                irFieldId = rec?.[0]?.product_template_field_id?.[0] || null;
                const attrName = rec?.[0]?.original_name || f.name;

                if (!irFieldId) {
                    const fields = await this._read(
                        "ir.model.fields",
                        [
                            ["model", "in", ["product.template", "product.product"]],
                            ["name", "=", attrName],
                        ],
                        ["id", "name", "field_description", "model"]
                    );

                    if (fields.length > 0) {
                        const exactMatch =
                            fields.find(x => x.name === attrName) || fields[0];

                        irFieldId = exactMatch.id;
                        techName = exactMatch.name;
                        label = exactMatch.field_description;
                        fieldModel = exactMatch.model;
                    } else {
                        this.props.renderer.notificationService.add(
                            "Could not find a field labeled '${attrName}'",
                            { type: "warning" }
                        );
                    }
                }
            }

            else if (f.source_model === "product.template") {
                techName = f.name;
                label = f.label || f.name;
                fieldModel = "product.template";
            }

            if (irFieldId && !techName) {
                const fld = await this._read(
                    "ir.model.fields",
                    [["id", "=", irFieldId]],
                    ["name", "field_description", "model"]
                );

                if (fld.length) {
                    techName = fld[0].name;
                    label = fld[0].field_description || f.name;
                    fieldModel = fld[0].model || fieldModel;
                }
            }

            if (!techName) techName = f.name;
            if (!label) label = techName;

            const finalObj = {
                field: techName,
                label: label,
            };
            updateFields.push(finalObj);
        }

        const finalPayload = {
            name: "product.enrich",
            payload: {
                products: products,
            },
            context: ctx,
            ai: ai,
            prompt_type: { type: promptTypeObj?.name || "" },
            count: { product: String(products.length) },
            update_attribute: {
                fields: updateFields.map(f => ({
                    field: f.field,
                    label: f.label,
                })),
            },
        };
        return finalPayload;
    }

    async getOdooSession() {
        if (this.env?.services?.user) {
            return {
                db: this.env.services.user.db,
                username: this.env.services.user.name,
            };
        }
        if (this.env?.services?.session) {
            return {
                db: this.env.services.session.db,
                username: this.env.services.session.username,
            };
        }
        if (window.odoo?.session_info) {
            return {
                db: window.odoo.session_info.db,
                username: window.odoo.session_info.username,
            };
        }
        return { db: "", username: "" };
    }

    goBack() {
        this.props.renderer.childBackCallback();
        TreeFormControllerBus.trigger("CLOSE_ACTIONS");
    }

    async triggerAIEnrichment(finalPayload) {
        finalPayload = JSON.parse(JSON.stringify(finalPayload));

        const url = "https://api.trigger.dev/api/v1/tasks/product-enrichment/trigger";

        const bodyData = {
            payload: {
                name: finalPayload.name,
                payload: { products: finalPayload.payload.products },
                context: finalPayload.context,
                ai: finalPayload.ai,
                prompt_type: finalPayload.prompt_type,
                count: finalPayload.count,
                update_attribute: finalPayload.update_attribute,
            },
        };

        const response = await fetch(url, {
            method: "POST",
            headers: {
                Authorization: "Bearer tr_prod_7ePqzXb9sWosq2amdx4D",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(bodyData),
        });

        const result = await response.json();
        const run_id = result?.id;

        if (run_id) {
            await this.createQueueLog(run_id, result);
        } else {
            this.props.renderer.notificationService.add(
                "No run_id received — skipping queue log",
                { type: "warning" }
            );
        }
    }

    async createQueueLog(run_id, response_json) {
        if (!(this.state.attributeValues.field_ids || []).length) {
            this.props.renderer.notificationService.add(
                "Please select at least one field for AI Enrichment.",
                { type: "warning" }
            );
            return;
        }

        const selected = this.props.renderer.env.model.root.selection || [];
        let allProductIds = [];

        for (const rec of selected) {
            if (rec.resModel === "product.product") {
                allProductIds.push(rec.resId);
            } else if (rec.resModel === "product.template") {
                const variants = await this._read(
                    "product.product",
                    [["product_tmpl_id", "=", rec.resId]],
                    ["id"]
                );
                allProductIds.push(...variants.map(v => v.id));
            }
        }

        const selectedFields = (this.state.attributeValues.field_ids || []).map(id => {
            const f = this.state.aiFields.find(x => x.id === id);
            return f ? f.name : id;
        });

        await this.props.controller.orm.create("ai.enrichment.queue.log", [
            {
                name: run_id,
                config_id: this.state.attributeValues.model_id,
                product_ids: [[6, 0, allProductIds]],
                prompt_type: this.state.promptTypes.find(
                    p => p.id == this.state.attributeValues.prompt_type
                )?.name,
                update_field: selectedFields.join(", "),
                event_payload: JSON.stringify(response_json),
                state: "queued",
            },
        ]);

        this.props.renderer.notificationService.add(`✅ AI Enrichment queued `, {
            type: "success",
        });
    }

    async loadAIData() {
        const configs = await this._read("ai.enrichment.config", [], ["provider"]);
        const uniqueProviders = [...new Set(configs.map(c => c.provider))];

        this.state.aiProviders = uniqueProviders.map(p => ({
            value: p,
            label: (p || "Unknown").toUpperCase(),
        }));

        this.state.aiModels = await this._read(
            "ai.enrichment.config",
            [],
            ["id", "name", "provider", "code", "api_key", "api_url", "password"]
        );

        // Only fields where ai.enrichment.field.is_enrichable = true
        const fields = await this._read(
            "ai.enrichment.field",
            [["is_enrichable", "=", true]],
            ["id", "name", "source_model", "source_id"]
        );

        const productAttrIds = fields
            .filter(f => f.source_model === "product.attribute")
            .map(f => f.source_id);
        const generalAttrIds = fields
            .filter(f => f.source_model === "general.attribute")
            .map(f => f.source_id);

        let productAttrs = [];
        if (productAttrIds.length) {
            productAttrs = await this._read(
                "product.attribute",
                [["id", "in", productAttrIds]],
                ["id", "display_type", "company_id"]
            );
        }
        const productAttrMap = Object.fromEntries(productAttrs.map(a => [a.id, a]));

        let generalAttrs = [];
        if (generalAttrIds.length) {
            generalAttrs = await this._read(
                "general.attribute",
                [["id", "in", generalAttrIds]],
                ["id", "is_ai_enrichable"]
            );
        }
        const generalAttrMap = Object.fromEntries(generalAttrs.map(a => [a.id, a]));

        const ptFieldInfo = await this.props.controller.orm.call(
            "product.template",
            "fields_get",
            [[]]
        );
        const activeCompanyId = this.env.services.company.currentCompany.id;

        let filtered = [];
        for (const f of fields) {
            if (f.source_model === "product.attribute") {
                const rec = productAttrMap[f.source_id];
                if (!rec) continue;
                const isText = ["text", "textarea"].includes(rec.display_type);
                const companyOK = !rec.company_id || rec.company_id[0] === activeCompanyId;
                if (isText && companyOK) filtered.push(f);
            }

            if (f.source_model === "product.template") {
                const info = ptFieldInfo[f.name];
                if (info && ["text", "char"].includes(info.type)) {
                    filtered.push(f);
                }
            }

            if (f.source_model === "general.attribute") {
                const rec = generalAttrMap[f.source_id];
                if (rec && rec.is_ai_enrichable === true) {
                    filtered.push(f);
                }
            }
        }

        this.state.aiFields = filtered;
        this.state.filteredAiFields = [...filtered];

        this.state.promptTypes = await this._read("ai.prompt.type", [], ["id", "name"]);

        const selection = this.props.renderer.env.model.root.selection || [];
        this.state.productCount = selection.length;
    }

    async getData() {
        if (this.props.action.action === "CHANGE_FAMILY") {
            const activeCompanyIds = this.env.services.company.activeCompanyIds;
            this.state.allFamilies = await this._read(
                "family.attribute",
                [["company_id", "in", activeCompanyIds]],
                ["id", "name"]
            );
        } else if (this.props.action.action === "ADD_TO_CATEGORIES") {
            const cats = await this._read(
                "pim.category",
                [["company_id", "in", [this.props.renderer.props.list.currentCompanyId]]],
                ["id", "name", "parent_id"]
            );
            this.state.allCategories = this.listToTree(cats);
        }
    }

    onValueChange(event) {
        const value = event.target.value;
        const name = event.target.name;

        if (name === "provider") {
            this.state.attributeValues["provider"] = value;
            this.state.aiFilteredModels = this.state.aiModels.filter(
                m => m.provider === value
            );
            if (this.state.aiFilteredModels.length > 0) {
                this.state.attributeValues["model_id"] = this.state.aiFilteredModels[0].id;
            }
            return;
        }

        if (name === "field_ids") {
            const opts = Array.from(event.target.selectedOptions).map(o => Number(o.value));
            this.state.attributeValues[name] = opts;
            return;
        }

        this.state.attributeValues[name] = value;
    }

    applyChanges() {
        for (const attrId of this.state.attributes) {
            if (!Object.keys(this.state.attributeValues).includes(attrId)) {
                this.props.renderer.notificationService.add(
                    "Please select value for all selected attributes.",
                    { type: "warning" }
                );
                return;
            }
        }

        if (this.state.attributeValues.field_ids) {
            this.state.attributeValues.field_ids = Array.from(
                this.state.attributeValues.field_ids
            );
        }

        this.props.renderer.dialogService.add(ConfirmationDialog, {
            title: "Are you sure want to confirm the changes?",
            body: `You are about to update the attribute values for ${
                this.props.renderer.env.model.root.selection.length
            } products.`,
            confirm: async () => {
                if (this.props.action.action === "AI_ENRICHMENT") {
                    if (!(this.state.attributeValues.field_ids || []).length) {
                        this.props.renderer.notificationService.add(
                            "Please select at least one field for AI Enrichment.",
                            { type: "warning" }
                        );
                        return;
                    }

                    const payload = await this.buildFinalPayload();
                    await this.triggerAIEnrichment(payload);

                    setTimeout(() => {
                        this.props.renderer.notificationService.add(
                            "✅ AI Enrichment queued successfully!",
                            { type: "success", sticky: false }  // auto-dismiss normally
                        );
                    }, 50);

                    localStorage.setItem("ai_enrichment_done", "true");

                    this.props.controller.changeStep("action_selection");

                    setTimeout(() => {
//                        this.env.services.action.doAction({
//                            type: "ir.actions.client",
//                            tag: "reload",
//                        });
                           this.goBack();
                    });
                    this.goBack();
                } else {
                    this.props.controller.saveChanges(this.state.attributeValues);
                }
            },
            cancel: () => {},
        });
    }

    changeStep(step) {
        this.props.controller.changeStep(step);
    }

    listToTree(data, options = {}) {
        const ID = options.idKey || "id";
        const PID = options.parentKey || "parent_id";
        const CHILD = options.childrenKey || "children";

        const map = {};
        data.forEach(item => {
            item[CHILD] = [];
            map[item[ID]] = item;
        });

        const roots = [];
        data.forEach(item => {
            const pid = item[PID] ? item[PID][0] : null;
            if (pid && map[pid]) {
                map[pid][CHILD].push(item);
            } else {
                roots.push(item);
            }
        });

        return roots;
    }
}
