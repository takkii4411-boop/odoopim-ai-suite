/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { useService, useBus } from "@web/core/utils/hooks";
import { TextField, ListTextField } from "@web/views/fields/text/text_field";
import { CharField } from "@web/views/fields/char/char_field";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useEffect } from "@odoo/owl";

export class MasterProductListRender extends ListRenderer {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.viewId = null;
        const viewId = this.env.services.orm.searchRead(
        "ir.model.data",
        [["name", "=", 'view_product_creation_split_view_custom']],
        ["res_id"]
        ).then(result => this.viewId = result[0].res_id)

    }

    
    async onCellClicked(record, column, ev) {
        super.onCellClicked(...arguments);
        // await this.orm.call("product.template", "custom_product_open_form_view", [record.resId]);

        // this.action.doAction({
        //     name: "Products",
        //     type: 'ir.actions.act_window',
        //     res_model: 'product.template',
        //     view_mode: 'form',
        //     views: [[false, 'form']],
        //     view_id: this.viewId,
        //     res_id :record.resId, 
        //     target:'current',
        //     context: {no_breadcrumbs: true,
               
        //     }
        // });
        
        await this.action.doAction({
            name: "Products",
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            view_mode: 'form',
            views: [[this.viewId, 'form']],
            res_id: record.resId,
            target: 'current',
            view_id: this.viewId,  // optional
            context: {
                no_breadcrumbs: true,
            },
        });
    }

}
ListRenderer.prototype.addOptionLine = function () {
    this.add();
};

export class MasterProductFieldOne2Many extends X2ManyField {
    static components = {
        ...X2ManyField.components,
        ListRenderer: MasterProductListRender,
    };
}



export const masterProductFieldOne2Many = {
    ...x2ManyField,
    component: MasterProductFieldOne2Many,
    additionalClasses: [...x2ManyField.additionalClasses || [], "o_field_one2many"],
};


registry.category("fields").add("master_product_one2many", masterProductFieldOne2Many);


