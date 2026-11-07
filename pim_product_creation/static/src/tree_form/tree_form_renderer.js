/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TreeFormRenderer } from "@odoopim_split_widget/views/tree_form_view/tree_form_renderer";
import { ProductCreation } from "@pim_product_creation/create_product/product_creation";
import { TreeFormControllerBus } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";

TreeFormRenderer.components = {
    ...TreeFormRenderer.components,
    ProductCreation,
}
patch(TreeFormRenderer.prototype, {
    triggerClose(){
        TreeFormControllerBus.trigger('CLOSE_ACTIONS');
    }
});