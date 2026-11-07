/** @odoo-module **/

import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";

const defaultProductFields = ["sequence", "default_code", "name", "list_price", "standard_price", "categ_id", "type"];


export class PrmExportDataDialog extends ExportDataDialog {
    /*
    * Overwrite to be able to assign default fields
    */
    setDefaultExportList() {
        if (this.state.isCompatible) {
            this.state.exportList = this.state.exportList.filter(
                ({ name }) => this.knownFields[name]
            );
        } else {
            // we use on such approach instead of filtering to save the order of fields and to loop over a short array
            const exportList = [];
            const knownFields = this.knownFields;
            defaultProductFields.forEach(function (name) { exportList.push(knownFields[name]) });
            this.state.exportList = exportList;
        }
    }
};
