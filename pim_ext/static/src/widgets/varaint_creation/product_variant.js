/** @odoo-module **/

import { Component, useState, onWillStart, useRef } from "@odoo/owl";
import { Record } from "@web/model/relational_model/record";
import { useService } from "@web/core/utils/hooks";
import { TreeFormControllerBus } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";

export class ProductVariantCreation extends Component {
    static template = "pim_navabrindit.ProductVariantCreation";
    static props = {
        name: {type: String},
        resModel : {type: String},
        resId: {type: Number},
        popup: {type: Object, optional: true}
    };
    setup(){
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            variant_ids : [],
            resId: false,
            products : [{val_ids:[],product:{
                'name': this.props.name,
                'product_template_variant_value_ids': [],
                'product_tmpl_id': this.props.resId,
                'sku': false,
            }},],
        })
        onWillStart(async () => {
            this.fetch_product_variant_lines();
        });
        console.log(this)
    }
    async fetch_product_variant_lines(){
        const attribute_lines = await this.orm.searchRead(
            "product.template.attribute.line",
            [['product_tmpl_id','=', this.props.resId]],
            ["id"]
        );
        const attribute_line_ids = attribute_lines.map(l => l.id);

        const variant_values = await this.orm.searchRead(
            "product.template.attribute.value",
            [['attribute_line_id','in', attribute_line_ids]],
            ["id",'name','attribute_line_id']
        );
        console.log(variant_values)
        const groupedByAttributeLine = {};

        for (const value of variant_values) {
            const [lineId, lineName] = value.attribute_line_id;

            if (!groupedByAttributeLine[lineId]) {
                groupedByAttributeLine[lineId] = {
                    attribute_line_id: lineId,
                    attribute_line_name: lineName,
                    values: [],
                };
            }

            groupedByAttributeLine[lineId].values.push({
                id: value.id,
                name: value.name,
            });
        }
        this.state.variant_ids = Object.values(groupedByAttributeLine);
        console.log(groupedByAttributeLine)
    }
    onClickRemove(p_index){
        this.state.products = this.state.products.filter((_, i) => i !== p_index);
    }
    onClickAdd(){
        this.state.products.push({
            val_ids: [],
            resId: false,
            product: {
                name: this.props.name,
                product_template_variant_value_ids: [],
                product_tmpl_id: this.props.resId,
                sku: false,
            },
        });
    }
    onChangeSelect(ev, attributeLineId, productIndex) {
        const valueId = parseInt(ev.target.value);
        if (!valueId) return;

        const product = this.state.products[productIndex];

        product.val_ids.push({
            attribute_line_id: attributeLineId,
            value_id: valueId,
        });

        product.product.product_template_variant_value_ids = [
            [6, 0, product.val_ids.map(v => v.value_id)]
        ];
    }
    onChangeName(ev, p_index){
        var value = ev.target.value;
        if (!value) return;
        const product = this.state.products[p_index];
        product.product['name'] = value;
    }
    onChangeSku(ev, p_index){
        var value = ev.target.value;
        if (!value) return;
        const product = this.state.products[p_index];
        product.product['sku'] = value;
    }
    async onClickCreate() {
        const existingProducts = await this.orm.searchRead(
            "product.product",
            [["product_tmpl_id", "=", this.props.resId]],
            ["product_template_variant_value_ids"]
        );
        const existingCombinations = new Set(
            existingProducts
                .filter(p => Array.isArray(p.product_template_variant_value_ids))
                .map(p =>
                    p.product_template_variant_value_ids
                        .slice()          // clone
                        .sort((a, b) => a - b)
                        .join(",")
                )
        );
        const productsToCreate = this.state.products
            .map(p => p.product)
            .filter(p => {
                const ids = Array.isArray(p.product_template_variant_value_ids)
                    ? p.product_template_variant_value_ids
                    : [];

                const key = [...ids].sort((a, b) => a - b).join(",");

                return ids.length && !existingCombinations.has(key);
            });

        if (!productsToCreate.length) {
            this.env.services.notification.add(
                "All selected variant combinations already exist.",
                { type: "warning" }
            );
            return;
        }

//        console.log("productsToCreate", productsToCreate)
//        for(const product in productsToCreate){
//            await this.orm.create("product.product", [product]);
//        }
        await this.orm.call("product.product", "create", [productsToCreate])

        this.action.doAction({
            type: "ir.actions.client",
            tag: "display_notification",
            params: {
                "type": "success",
                "message": "Variants Success-fully created"
            },
        });
        if(this.props.popup){
            this.props.popup.close();
        }
        TreeFormControllerBus.trigger('CLOSE_ACTIONS');
    }
}