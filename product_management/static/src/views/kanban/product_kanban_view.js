/** @odoo-module **/

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { ProductKanbanController } from "./product_kanban_controller";
import { ProductKanbanModel } from "./product_kanban_model";
import { ProductKanbanRenderer } from "./product_kanban_renderer";
import { ProductSearchModel } from "../search/product_search_model";

export const productKanbanView = {
    ...kanbanView,
    SearchModel: ProductSearchModel,
    Controller: ProductKanbanController,
    Model: ProductKanbanModel,
    Renderer: ProductKanbanRenderer,
    searchMenuTypes: ["filter", "favorite"],
};

registry.category("views").add("product_kanban", productKanbanView);
