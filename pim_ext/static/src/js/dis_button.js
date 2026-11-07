/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
const { Component, onWillStart, useState } = owl;
const componentModel = "product.brand";
import { registry } from "@web/core/registry";
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { ListRenderer } from "@web/views/list/list_renderer";
import { unique } from "@web/core/utils/arrays";

export class ProductBrandListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    showarchived() {
        var domain = "[['active', 'in', [false, true]]]";
        var view_id = this.env.config.viewId;
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.management',
            name: 'Product Management',
            view_mode: 'list,form',
            view_type: 'list,form',
            views: [[this.env.config.viewId || false, "list"], [false, "form"]],
            domain: domain,
            target: 'main'
        });
    }

    hidearchived() {
        var domain = "[['active', 'in', [true]]]";
        var view_id = this.env.config.viewId;
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.management',
            name: 'Product Management',
            view_mode: 'list,form',
            view_type: 'list,form',
            views: [[this.env.config.viewId || false, "list"], [false, "form"]],
            domain: domain,
            target: 'main'
        });
    }
};

ProductBrandListController.template = "product_control_panel.productBrandListView";

export const productBrandListView = {
    ...listView,
    Controller: ProductBrandListController,
};

registry.category("views").add("product_brand_list", productBrandListView);