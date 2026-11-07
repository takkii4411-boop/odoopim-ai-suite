/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { deleteConfirmationMessage, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { WarningDialog } from "@web/core/errors/error_dialogs";

patch(ListRenderer.prototype, {
    async onDeleteRecord(record) {
        this.keepColumnWidths = true;
        const editedRecord = this.props.list.editedRecord;
        if (editedRecord && editedRecord !== record) {
            const leaved = await this.props.list.leaveEditMode();
            if (!leaved) {
                return;
            }
        }
        if (this.activeActions.onDelete) {

            const dialogService = this.env.services.dialog;
            const orm = this.env.services.orm;
            console.log("delete dialog box ----------------", record)
            console.log("this.props.list.resModelx ----------------", this.props.list.resModel)
//            console.log("family id ----------------", record.evalContext.parent.id)
            var families = await orm.searchRead("family.attribute", [['id','=',record.evalContext.parent.id]], ["id","name", "exist_attribute_ids"]);
            var products = await orm.searchRead("product.template", [['family_id','=',record.evalContext.parent.id]], ["id","name"]);
            console.log("products == ", products, products.length)
            console.log("families == ", families, families.length)
            if ((this.props.list.resModel == 'family.attributes') && (products.length > 0)){
                dialogService.add(ConfirmationDialog, {
                    title: _t("Confirmation"),
                    body: _t("The Attribute cannot be deleted, as it is already linked with %s  products.",products.length),
                    confirmLabel: _t("Ok"),
                    confirm: async () => {
                        await this.activeActions.onDelete(record);
                    },
                    cancel: () => {},
                });
            }
            else if ((this.props.list.resModel == 'product.attribute')){
                dialogService.add(WarningDialog, { title: _t("Warning") ,message:_t("The Family cannot be deleted, as it is already linked with ${products.length} products.") });
            }
            else if ((this.props.list.resModel == 'attribute.group') && (products.length > 0)){
                dialogService.add(ConfirmationDialog, {
                    title: _t("Confirmation"),
                    body: _t("The Attribute cannot be deleted, as it is already linked with %s  products.",products.length),
                    confirmLabel: _t("Ok"),
                    confirm: async () => {
                        await this.activeActions.onDelete(record);
                    },
                    cancel: () => {},
                });
            }
            else{
                dialogService.add(ConfirmationDialog, {
                    title: _t("Confirmation"),
                    body: _t("Are you sure you want to delete this record?"),
                    confirmLabel: _t("Ok"),
                    confirm: async () => {
                        await this.activeActions.onDelete(record);
                    },
                    cancel: () => {},
                });
            }
        }
    }
});
