/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { ProductKanbanRecord } from "./product_kanban_record";
import { ProductManager } from "@product_management/components/product_manager/product_manager";
import { ProductNavigation } from "@product_management/components/product_navigation/product_navigation";


export class ProductKanbanRenderer extends KanbanRenderer {
    /*
    * Prepare props for the ProductManager (right navigation & mass actions component)
    */
    getProductManagerProps() {
        return {
            currentSelection: this.props.list.selection || [],
            selection: this.props.list.model.selectedRecords || [],
            kanbanModel: this.props.list.model,
            canCreate: this.props.archInfo.activeActions.create,
        };
    }
    /*
    * The method to ProductNavigation (left navigation)
    */
    getProductNavigationProps() {
        return {
            kanbanList: this.props.list,
        }
    }
};

ProductKanbanRenderer.template = "product_management.ProductsKanbanRenderer";
ProductKanbanRenderer.components = Object.assign({}, KanbanRenderer.components, {
    ProductManager,
    ProductNavigation,
    KanbanRecord: ProductKanbanRecord,
});
