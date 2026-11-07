/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
const { Component, onWillStart, useState } = owl;
const componentModel = "product.template";
import { registry } from "@web/core/registry";
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { ListRenderer } from "@web/views/list/list_renderer";
import { unique } from "@web/core/utils/arrays";

class SplitAttributeView extends ListController {
    setup() {
        super.setup();
        this.state = useState({
            isOpen: false, // Control visibility of the form
        });
    }

    async _onClickCreateAttribute(event) {
        event.stopPropagation(); // Prevent event bubbling
        const viewId = await this._rpc({
            model: 'ir.ui.view',
            method: 'get_view_id',
            args: [['pim.attribute.type']],
        });

        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Create Attribute Type',
            res_model: 'pim.attribute.type',
            view_mode: 'form',
            view_id: viewId,
            target: 'inline', // Use inline target for split view
        });
    }
}

// Register the component in the view registry
registry.add('split_attribute_view', SplitAttributeView);