/** @odoo-module */

import { Component, useState, onWillStart, useRef } from "@odoo/owl";
import { TreeFormControllerBus } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { ProductVariantCreation } from "@pim_ext/widgets/varaint_creation/product_variant";

const PRODUCT_CREATION_ACTIONS = [{'name': 'Product', 'type':'PRODUCT', 'image':'/pim_product_creation/static/src/img/icon-product.svg'},
                            {'name':'Product Model','type':'MODEL','image':'/pim_product_creation/static/src/img/icon-model.svg'},
                            {'name':'Bundle Product','type':'BUNDLE','image':'/pim_product_creation/static/src/img/icon-bundle-group.svg'},
                            {'name':'Grouped Product','type':'GROUP','image':'/pim_product_creation/static/src/img/icon-bundle-group.svg'}]

export class ProductCreation extends Component{
    static template = "pim_product_creation.ProductCreation";
    static components = { ProductVariantCreation }
    static props = {
        resModel: { type: String },
        treeForm : Object,
    };
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            step : 0,
            menu: PRODUCT_CREATION_ACTIONS,
            menu_type: false,
            families: [],
            family_variants: [],
            products : [],
            resId: false,
            button_name:"Next",
            loading: false,
            resize: false,
        });
        // new state for variant creation purpose
        this.variant = useState({
            products : [],
        })
        onWillStart(async () => {
            // Load families with variant_line_ids
            this.state.loading = true;
            const families = await this.orm.searchRead(
                "family.attribute",
                [["company_id", "in", [this.props.treeForm.props.list.currentCompanyId]]],
                ["id", "name", "variant_line_ids", "family_attribute_ids"]
            );
            // Collect all variant_line_ids across families
            const allVariantLineIds = families.flatMap(fam => fam.variant_line_ids || []);

            let variantLineMap = {};
            let variantMap = {};

            if (allVariantLineIds.length) {
                // Load variant lines (with variant_ids)
                const variantLines = await this.orm.searchRead(
                    "family.variant.line", // replace with your actual model
                    [["id", "in", allVariantLineIds]],
                    ["id", "name", "variant_ids"]
                );

                // Collect all variant_ids across variant lines
                const allVariantIds = variantLines.flatMap(line => line.product_attribute_ids || []);

                // Load variant records (id + name)
                if (allVariantIds.length) {
                    const variants = await this.orm.searchRead(
                        "product.attribute", // replace with your actual variant model
                        [["id", "in", allVariantIds]],
                        ["id", "name"]
                    );
                    variantMap = Object.fromEntries(variants.map(v => [v.id, v.name]));
                }

                // Build variant line map with nested variant details
                variantLineMap = Object.fromEntries(
                    variantLines.map(line => [
                        line.id,
                        {
                            id: line.id,
                            name: line.name,
                            variants: (line.variant_ids || []).map(vid => ({
                                id: vid,
                                name: variantMap[vid] || "Unknown",
                            })),
                        },
                    ])
                );
            }

            // Merge into family structure
            this.state.families = families.map(fam => ({
                ...fam,
                variant_lines: (fam.variant_line_ids || []).map(vlid => variantLineMap[vlid]),
            }));
            if(this.state.families.length >= 1){
                this.onchangeFamily(this.state.families[0].id);
            }
            this.state.loading = false;
        });
    }
    changeAction(type){
        const result = PRODUCT_CREATION_ACTIONS.find(item => item.type === type);
        this.state.menu_type = result;
    }
/*    async prepare_variant_attributes(value) {
        const family_variant = this.state.family_variants.find(rec => rec.id == value);
        if (!family_variant) {
            return [];
        }
        const variant_ids = (family_variant.variants || []).map(x => x.id);
        if (!variant_ids.length) {
            return [];
        }
        // Fetch attribute values for these attributes
        const attribute_values = await this.orm.searchRead(
            "product.attribute.value",
            [["attribute_id", "in", variant_ids]],
            ["id", "attribute_id", "name"]
        );
        // Group by attribute_id
        const grouped = {};
        attribute_values.forEach(v => {
            const attr_id = v.attribute_id[0];
            if (!grouped[attr_id]) {
                grouped[attr_id] = {
                    attribute_id: attr_id,
                    value_ids: [],
                };
            }
            grouped[attr_id].value_ids.push(v.id);
        });
        const attribute_lines = Object.values(grouped).map(g => [0, 0, g]);
        return attribute_lines;
    }*/
    async prepare_variant_attributes(value, resId) {
        const family_variant = this.state.family_variants.find(
            rec => rec.id === value
        );
        if (!family_variant) {
            return [];
        }

        const variant_ids = (family_variant.variants || []).map(v => v.id);
        if (!variant_ids.length) {
            return [];
        }

        // Fetch attribute values
        const attribute_values = await this.orm.searchRead(
            "product.attribute.value",
            [["attribute_id", "in", variant_ids]],
            ["id", "attribute_id"]
        );

        // Group value IDs by attribute
        const grouped = {};
        for (const v of attribute_values) {
            const attrId = v.attribute_id[0];
            if (!grouped[attrId]) {
                grouped[attrId] = [];
            }
            grouped[attrId].push(v.id);
        }

        // Build commands in your desired structure
        const commands = [];
        for (const [attributeId, valueIds] of Object.entries(grouped)) {
            commands.push({
                attribute_id: Number(attributeId),
                product_tmpl_id: resId,
                value_ids: [[6, 0, valueIds]],
                active: true,
            });
        }
        return commands;
    }
    async CREATE_PRODUCT(step){
        // back after creating product
        if(this.state.step == 2 && step == -1){
            this.state.step = 0;
            this.state.products = [];
            this.button_name();
            return true;
        }
        // viewing product
        if(this.state.step == 2 && step == 1){
            if(this.state.products.length >= 1){
                var record = this.props.treeForm.props.list.records.find(item => item.data.id == this.state.products[0].id)
                this.props.treeForm.openRecordWithChanges(record)
            }
            return true;
        }
        // save product after typing vals
        if(this.state.step == 1 && step == 1){
            this.state.loading = true;
            const form = document.getElementById('form_'+this.state.menu_type.type);
            var form_data = this.submitForm(form);
            const create_prod = await Promise.resolve(this.create_product_with_data(form_data, true));
            if(create_prod){
                if(this.props.resModel == 'product.template'){
                    await Promise.resolve(this.props.treeForm.props.list.model.load());
                    let record = null;
                    for (let i=0; i<10;i++){
                        record = this.props.treeForm.props.list.records.find(
                            item => item.resId == create_prod.id
                        );
                        if(record){
                            break;
                        }
                        await new Promise(resolve => setTimeout(resolve,200))
                    }
                    if(record){
                        await Promise.resolve(this.props.treeForm.openRecordWithChanges(record));
                    }
                }
                else{
                    const view_id = await Promise.resolve(this.orm.call("product.template", 'get_form_view_id', [parseInt(create_prod.id)], {}));
                    await Promise.resolve(this.actionService.doAction({
                        name: "Variant Product",
                        res_model: "product.template",
                        res_id: parseInt(create_prod.id),
                        view_mode: "form",
                        views: [[view_id,"form"]],
                        type: "ir.actions.act_window",
                        target: "new",
                    }));
                    this.state.step = 0;
                    this.state.products = [];
                }
                this.state.loading = false;
            }
            this.button_name();
            return true;
        }
    }
    async CREATE_PRODUCT_MODEL(step){
        // back after creating product
        if(this.state.step == 2 && step == -1){
            this.state.step = 0;
            this.state.products = [];
            this.button_name();
            return true;
        }
        // save and close product variants
        if(this.state.step == 2 && step == 1){
            this.state.loading = true;
            for(const product of this.variant.products){
                await Promise.resolve(this.orm.write('product.product',[product.id],{'sku':product.sku}));
            }
            this.state.loading = false;
            this.state.step = 0;
            this.state.products = [];
            this.variant.products = [];
            this.button_name();
            return true;
        }
        // save product data to state after typing vals
        if(this.state.step == 1 && step == 1){
            this.state.loading = true;
            const form = document.getElementById('form_'+this.state.menu_type.type);
            var form_data = await this.submitForm(form);
            this.state.products = [Object.assign({}, form_data)];
            if(form_data){
//                var attribute_line_ids = await Promise.resolve(this.prepare_variant_attributes(form_data.variant_id));
//                form_data['attribute_line_ids'] = attribute_line_ids;
                const create_prod = await Promise.resolve(this.create_product_with_data(form_data, false));
//                this.variant.products = await this.orm.searchRead('product.product',[['product_tmpl_id','=', form_data.id]],['id','display_name','sku',]);
                this.state.resId = form_data.id;
                const commands = await Promise.resolve(this.prepare_variant_attributes(form_data.variant_id, form_data.id));
                await this.orm.create("product.template.attribute.line", commands)
                await Promise.resolve(this.props.treeForm.props.list.model.load());
                this.state.step = this.state.step + step;
            }
            this.button_name();
            this.state.loading = false;
            return true;
        }
    }
    async nextStep(step){
        if(this.state.menu_type.type == 'PRODUCT'){
            const product = await this.CREATE_PRODUCT(step);
            if(product){
                return;
            }
        }
        if(this.state.menu_type.type == 'MODEL'){
            const product_model = await this.CREATE_PRODUCT_MODEL(step);
            if(product_model){
                return;
            }
        }
        if(this.state.menu_type.type == 'BUNDLE'){
            // TODO create bundle product functionality
            return;
        }
        if(this.state.menu_type.type == 'GROUP'){
            // TODO create group product functionality
            return;
        }
        if(this.state.menu_type){
            this.state.step = this.state.step + step;
        }
        this.button_name();
    }
    button_name(){
        if(this.state.step == 1 && this.state.menu_type.type == "PRODUCT"){
           this.state.button_name = "Save";
           return;
        }
        if(this.state.step == 1 &&
            this.state.menu_type.type == "MODEL"){
            this.state.button_name = "Save & Next";
            return;
        }
        if(this.state.step == 2 && this.state.menu_type.type == "PRODUCT"){
            this.state.button_name = "View";
            return;
        }
        if(this.state.step == 2 && this.state.menu_type.type == 'MODEL'){
            this.state.button_name = "Save & Close";
            return;
        }
        this.state.button_name = "Next";
        return;
    }
    submitForm(form){
        const formData = new FormData(form);
        var data = Object.fromEntries(formData.entries());
        if (!form.checkValidity()) {
            form.classList.add("was-validated");
            this.state.loading = false;
            return false;
        }
        data = this.convertFormValues(data);
        return data;
    }
    async create_product_with_data(data, create_product_product) {
        try {
            const [product] = await this.orm.create("product.template", [data],{context: {'create_product_product': create_product_product}});
            data['id'] = product;
            this.state.products = [data];
            return data;
        } catch (error) {
            console.error("Error creating product:", error);
            return false;
        }
    }
    convertFormValues(data) {
        // format form data as per data types
        const fieldTypes = this.get_fields_types();
        for (const [key, type] of Object.entries(fieldTypes)) {
            if (!(key in data)) continue; // skip missing fields
            let value = data[key];
            if (value === "" || value === null || value === undefined) {
                data[key] = null;
                continue;
            }
            switch (type) {
                case "int":
                    data[key] = parseInt(value, 10) || 0;
                    break;
                case "float":
                    data[key] = parseFloat(value) || 0.0;
                    break;
                case "bool":
                    data[key] = value === "true" || value === true;
                    break;
                case "char":
                default:
                    data[key] = String(value);
                    break;
            }
        }
        return data;
    }
    get_fields_types(){
        //field types will be defined here for convertion of data
        return {
            'family_id':'int',
            'name':'char',
            'sku':'char',
            'variant_id':'int',
        }
    }
    triggerClose(){
        if(this.state.step == 0){
            TreeFormControllerBus.trigger('CLOSE_ACTIONS');
        }
        else{
            this.nextStep(-1)
        }
    }
    resize(){
        if(!this.state.resize){
            this.props.treeForm.setLeftRightWidth(40,60);
            this.state.resize = true;
        }
        else{
            this.props.treeForm.setLeftRightWidth(60,40);
            this.state.resize = false;
        }
    }
    onchangeFamily(val){
//        update the family variants
        const family_id = parseInt(val);
        if(!family_id){
            this.state.family_variants = [];
            return;
        }
        const family_variants = this.state.families.find(fam => fam.id == family_id);
        if(!family_variants || !family_variants.variant_lines.length){
            this.state.family_variants = [];
            return;
        }
        this.state.family_variants = family_variants.variant_lines;
        return;
    }
    async editProduct(ev) {
        const productId = ev.currentTarget.dataset.id;
        if(productId){
            const view_id = await this.orm.call("product.product", 'get_form_view_id', [parseInt(productId)], {});
            this.actionService.doAction({
                name: "Variant Product",
                res_model: "product.product",
                res_id: parseInt(productId),
                view_mode: "form",
                views: [[view_id,"form"]],
                type: "ir.actions.act_window",
                target: "new",
            });
        }
    }
    async deleteProduct(ev) {
        const productId = ev.currentTarget.dataset.id;
        this.dialogService.add(ConfirmationDialog, {
            body: _t("Are you sure that you want to remove this item?"),
            confirm: async () => {
                try {
                    await this.orm.unlink("product.product", [parseInt(productId)]);
                    this.variant.products = this.variant.products.filter(p => p.id != productId);
                    this.notification.add(
                        _t("Item removed successfully"),
                        { type: "success" }
                     );
                     return;
                } catch (error) {
                    this.notification.add(
                        _t("Item can't be removed"),
                        { type: "danger" }
                     );
                }
            },
            cancel: () => {},
        });
    }
    get variant_count(){
        return this.variant.products?.length || 0;
    }
}
