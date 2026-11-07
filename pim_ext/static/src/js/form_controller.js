/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useEffect,useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


patch(FormController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.viewService = useService("view");
        // reactive state for select_variant_id
        useEffect(() => {
            const variantId = this.model?.root?.data?.select_product_variant_id || false;
            if (variantId) {
                this.onVariantChange(variantId);
            }
        }, () => [this.model?.root?.data?.select_product_variant_id]);
    },
    async onVariantChange(variantId) {
        if (!variantId) return;
        this.orm.searchRead()
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "product.product",
            res_id: variantId[0],
            views: [[false, "form"]],
            target: "new", // embed inside current form
        });
    },
});