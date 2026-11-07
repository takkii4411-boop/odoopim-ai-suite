/** @odoo-module */

import {extractFieldsFromArchInfo} from "@web/model/relational_model/utils";
import {ListRenderer} from "@web/views/list/list_renderer";
import {FormRenderer} from "@web/views/form/form_renderer";
import {Record} from "@web/model/relational_model/record";
import {markRaw, onWillStart, useState, useEffect} from "@odoo/owl";
import {
    ConfirmationDialog
} from "@web/core/confirmation_dialog/confirmation_dialog";
import {useService} from "@web/core/utils/hooks";
import {parseXML} from "@web/core/utils/xml";
import {registry} from "@web/core/registry";
import {ExportDataDialog} from "@web/views/view_dialogs/export_data_dialog";
import {_t} from "@web/core/l10n/translation";

import {
    ActionController
} from "../../components/action_controller/action_controller";
import {Filters} from "../filters/filters";

import {
    TreeFormControllerBus
} from "@odoopim_split_widget/views/tree_form_view/tree_form_controller"

const viewRegistry = registry.category("views");


export class TreeFormRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.formViewService = useService("view");
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.treeFrom = useState({
            selectedAction: false,
            currentSequenceEditIndex: 0,
            recordChanges: {},
            bulkAction: false,
            isFormDirty: false,

        });
        this.numSwitch = true;
        onWillStart(async () => {
            const resModel = this.props.list.resModel;
            const formID = this.getFormViewId();
            const {
                fields,
                relatedModels,
                views: {form: {arch}}
            } = await this.formViewService.loadViews({
                context: this.props.list.context,
                resModel,
                views: [[formID, 'form']],
            }, {
                actionId: this.env.config.actionId,
            })
            const archXmlDoc = parseXML(arch);
            const viewProps = {
                arch: archXmlDoc,
                fields: fields,
                relatedModels: markRaw(relatedModels),
                resModel,
            }
            const view = viewRegistry.get('form');
            const {archInfo} = view.props(viewProps, view);
            const {activeFields} = extractFieldsFromArchInfo(
                archInfo,
                fields
            );
            Object.assign(this.treeFrom, {
                archInfo,
                fields,
                activeFields
            });
            // default show first record in the right sight form
//            if (this.props.list.count) {
//                this.onCellClicked(this.props.list.records[0]);
//            }


        })
        useEffect(
            () => {
                this.onPropsChanged(this.props);
            },
            () => [this.props.list?.domain, this.props.list?.groupBy, this.props.list?.count]
        );
        this.is_unfold = false;
        this.update_folded_custom()
        TreeFormControllerBus.addEventListener("OPEN_RECORD", function (ev) {
            const record = ev.detail.record || false;
            if (record) {
                this.treeFrom.current_record = record;
                this.props.openRecord(this.treeFrom.current_record)
            }
        }.bind(this));
    }

    closeFormView() {
        this.treeFrom.current_record = null;
        this.treeFrom.isFormDirty = false;
        this.setLeftRightWidth(100, 0);
    }


    async onFormSave() {
        if (!this.treeFrom.current_record || !this.treeFrom.isFormDirty) return;

        try {
            const saved = await this.treeFrom.current_record.save();
            if (saved) {
                await this.treeFrom.current_record.load();
                await this.props.list.model.load();
                this.treeFrom.isFormDirty = false;

                this.env.services.notification.add(
                    _t("Record saved successfully"),
                    {type: "success"}
                );
            }
        } catch (error) {
            console.error("Error saving record:", error);
            this.env.services.notification.add(
                _t("Failed to save record"),
                {type: "danger"}
            );
        }
    }


    async onFormDiscard() {
        if (!this.treeFrom.current_record) return;

        try {
            await this.treeFrom.current_record.discard();
            await this.treeFrom.current_record.load();
            this.treeFrom.isFormDirty = false;

            this.env.services.notification.add(
                _t("Changes discarded"),
                {type: "info"}
            );
        } catch (error) {
            console.error("Error discarding changes:", error);
        }
    }


    update_folded_custom() {
        if (this.resModel == 'product.product' && this.group_by_product_tmpl) {
            this.props.list.groups.forEach((group) => {
                if (!group.isFolded && group.count > 1) {
                    group.model._updateConfig(
                        group.config,
                        {isFolded: !group.config.isFolded},
                        {reload: false}
                    );
                }
            });
        }
    }

    onPropsChanged() {
        this.update_folded_custom()
    }

    set_is_unfold(group) {
//        group.isFolded = true;
        this.is_unfold = true;
        return this.is_unfold;
    }

    unset_is_unfold(group) {
//        group.isFolded = false;
        this.is_unfold = false;
        return this.is_unfold;
    }

    getFormViewId() {
        let id = false;
        for (const lst of this.env.config.views) {
            if (lst[1] === 'form') {
                id = lst[0];
                break;
            }
        }
        return id;
    }

    get resModel() {
        return this.props.list.resModel;
    }

    get group_by_product_tmpl() {
        if (this.props.list.isGrouped) {
            return this.props.list.groupBy.includes("product_tmpl_id");
        }
        return false;
    }

    // Sequence Edit
    get isFirstSequenceEdit() {
        return this.treeFrom.currentSequenceEditIndex === 0;
    }

    get isLastSequenceEdit() {
        return this.treeFrom.currentSequenceEditIndex === this.env.model.root.selection.length - 1;
    }

    get completePercentage() {
        return `${Math.floor(((this.treeFrom.currentSequenceEditIndex + 1) / this.env.model.root.selection.length) * 100)}%`;
    }

    getRecordNameByIndex(index) {
        if (index < 0 || index >= this.env.model.root.selection.length) {
            return '';
        }
        const record = this.env.model.root.selection[index];
        return record.name || (record.data && record.data.name) || '';
    }

    async saveAndNext() {
        if (this.isLastSequenceEdit) {
            this.treeFrom.recordChanges[this.treeFrom.current_record.resId] = this.treeFrom.current_record._changes;
            await this.SequenceEditSaveAll();
            this.treeFrom.currentSequenceEditIndex = 0;
            this.childBackCallback();
        } else {
            this.treeFrom.recordChanges[this.treeFrom.current_record.resId] = this.treeFrom.current_record._changes;
            this.nextSequenceEdit();
        }
    }

    async SequenceEditSaveAll() {
        try {
            // loop all the recordChanges and save
            let ids = Object.keys(this.treeFrom.recordChanges);
            if (ids.length === 0) {
                return;
            }
            ids = ids.map(id => parseInt(id));
            for (const id of ids) {
                const changes = this.treeFrom.recordChanges[id];
                if (changes) {
                    await this.env.services.orm.write(this.props.list.resModel, [id], changes);
                }
            }
            this.env.services.notification.add("All changes saved successfully.", {type: "success"});
        } catch (e) {
            console.error(e);
            this.env.services.notification.add("Somthing went wrong!", {type: "error"});
        }
    }

    nextSequenceEdit() {
        if (this.isLastSequenceEdit) {
            return;
        }
        this.treeFrom.currentSequenceEditIndex += 1;
        const record = this.env.model.root.selection[this.treeFrom.currentSequenceEditIndex];
        this.openRecordWithChanges(record);
    }

    previousSequenceEdit() {
        if (this.isFirstSequenceEdit) {
            return;
        }
        this.treeFrom.currentSequenceEditIndex -= 1;
        const record = this.env.model.root.selection[this.treeFrom.currentSequenceEditIndex];
        this.openRecordWithChanges(record);
    }

    async openRecordWithChanges(record) {
        await this.onCellClicked(record);
        const changes = this.treeFrom.recordChanges[record.resId];
        if (changes) {
            this.treeFrom.current_record._changes = changes;
        }
    }


    async bulkDuplicate() {
        return new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                body: _t("These products will be duplicated without their variants. Do you want to proceed?"),
                confirmLabel: _t("Yes, Proceed"),
                confirm: async () => {
                    try {
                        const recordIds = this.props.list.selection.map((rec) => rec.resId);
                        const resModel = this.props.list.resModel;

                        // Call Python backend with res_model
                        const results = await this.orm.call(
                            resModel,
                            "bulk_duplicate_products",
                            [recordIds, resModel]
                        );

                        // Handle results
                        if (results.success_count > 0) {
                            this._showSuccessNotification(results);
                            await this.props.list.model.load();

                            // Navigate to last duplicated product
                            if (results.last_duplicated_id) {
                                this._navigateToProduct(results.last_duplicated_id);
                            }

                            resolve(true);
                        } else {
                            this._showFailureNotification();
                            resolve(false);
                        }
                    } catch (error) {
                        this._showErrorNotification(error);
                        resolve(false);
                    }
                },
                cancel: () => resolve(false),
            });
        });
    }

    _showSuccessNotification(results) {
        let message = _t(`Successfully duplicated ${results.success_count} product(s).`);
        if (results.failed_count > 0) {
            message += _t(` ${results.failed_count} failed.`);
        }

        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "display_notification",
            params: {
                type: results.failed_count === 0 ? "success" : "warning",
                title: _t("Bulk Duplicate Completed"),
                message: message,
                sticky: false,
            },
        });
    }

    _showFailureNotification() {
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "display_notification",
            params: {
                type: "danger",
                title: _t("Bulk Duplicate Failed"),
                message: _t("All duplication attempts failed."),
                sticky: true,
            },
        });
    }

    _showErrorNotification(error) {
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "display_notification",
            params: {
                type: "danger",
                title: _t("Bulk Duplicate Error"),
                message: _t("An unexpected error occurred: ") + error.message,
                sticky: true,
            },
        });
    }

    _navigateToProduct(productId) {
        setTimeout(async () => {
            const duplicatedRecord = this.props.list.records.find(
                rec => rec.resId === productId
            );

            if (duplicatedRecord) {
                await this.onCellClicked(duplicatedRecord);
            }
        }, 300);
    }

    async bulkArchive() {
        return new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                body: _t("These products will be Archived. Do you want to proceed?"),
                confirmLabel: _t("Yes, Proceed"),
                confirm: async () => {
                    try {
                        // Delete records
                        await this.orm.write(
                            this.resModel,
                            this.props.list.selection.map(rec => rec.resId),
                            {'active': false}
                        );

                        // Success notification
                        this.actionService.doAction({
                            type: "ir.actions.client",
                            tag: "display_notification",
                            params: {
                                type: "success",
                                title: "Bulk Archive",
                                message: "Products Successfully Archived",
                                sticky: false,
                            },
                        });

                        // Reload the list
                        await this.props.list.model.load();
                    } catch (error) {
                        console.error("Error Archiving:", error);
                        this.actionService.doAction({
                            type: "ir.actions.client",
                            tag: "display_notification",
                            params: {
                                type: "danger",
                                title: "Bulk Archive",
                                message: "Failed to Archive products",
                                sticky: false,
                            },
                        });
                    }
                    resolve(true);
                },
                cancel: () => {
                    resolve(false);
                },
            });
        });
    }

    async bulk_delete_products() {
        return new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                body: _t("These products will be permanently deleted. Do you want to proceed?"),
                confirmLabel: _t("Yes, Proceed"),
                confirm: async () => {
                    try {
                        // Delete records
                        await this.orm.unlink(
                            this.resModel,
                            this.props.list.selection.map(rec => rec.resId)
                        );

                        // Success notification
                        this.actionService.doAction({
                            type: "ir.actions.client",
                            tag: "display_notification",
                            params: {
                                type: "success",
                                title: "Bulk Delete",
                                message: "Products Successfully Deleted",
                                sticky: false,
                            },
                        });

                        // Reload the list
                        await this.props.list.model.load();
                    } catch (error) {
                        console.error("Error deleting:", error);
                        this.actionService.doAction({
                            type: "ir.actions.client",
                            tag: "display_notification",
                            params: {
                                type: "danger",
                                title: "Bulk Delete",
                                message: "Failed to delete products",
                                sticky: false,
                            },
                        });
                    }
                    resolve(true);
                },
                cancel: () => {
                    resolve(false);
                },
            });
        });
    }

    async selectAction(action) {
        TreeFormControllerBus.trigger('CLOSE_ACTIONS');
        this.treeFrom.selectedAction = action;
        if (action === 'BULK_ACTION') {
            TreeFormControllerBus.trigger('BULK_ACTION_OPEN');
        }
        if (action === 'SEQUENTIAL_EDIT') {
            this.onCellClicked(this.env.model.root.selection[0]);
        }
        if (action === 'BULK_DELETE') {
            const confirmed = await this.bulk_delete_products();
            return;
        }
        if (action === 'BULK_EXPORT') {
            this.setLeftRightWidth(60, 40);
            return;
        }
        this.setLeftRightWidth(60, 40);
    }

    setLeftRightWidth(left, right) {
        document.getElementsByClassName('tree-form-tree')[0].style.width = left + '%';
        document.getElementsByClassName('tree-form-form')[0].style.width = right + '%';
    }

    unselectAll() {
        this.env.model.root.selection.forEach((record) => {
            record.toggleSelection(false);
        });
        this.env.model.root.selectDomain(false);
        // reset selected action
        this.treeFrom.selectedAction = false;
        TreeFormControllerBus.trigger('CLOSE_ACTIONS');
    }

    childBackCallback() {
        // reset selected action
        this.treeFrom.selectedAction = false;
        this.unselectAll();
        this.setLeftRightWidth(100, 0);
    }

    onStartTreeFormReSize(ev) {
        const parent = ev.target.parentElement;
        const left = parent.querySelector('.tree-form-tree');
        const right = parent.querySelector('.tree-form-form');
        const initialX = ev.clientX;

        const leftWidth = left.getBoundingClientRect().width;
        const rightWidth = right.getBoundingClientRect().width;

        const leftTable = left.querySelector('.o_list_table');
        const leftThElements = leftTable?.querySelectorAll('thead th') || [];
        const leftTdElements = leftTable?.querySelectorAll('tbody td') || [];

        // Calculate initial column width ratio
        const FIXED_WIDTHS = [40, 40];
        const fixedCols = [0, 1];
        const initialColumnWidths = Array.from(leftThElements).map(th => th.getBoundingClientRect().width);

        // Only calculate the total width of non-fixed columns
        const totalVariableWidth = initialColumnWidths.reduce((sum, width, index) =>
            fixedCols.includes(index) ? sum : sum + width, 0);

        // Calculate the proportion of each column to the variable width (fixed columns are set to 0)
        const columnProportions = initialColumnWidths.map((width, index) =>
            fixedCols.includes(index) ? 0 : width / totalVariableWidth);

        const resizeStoppingEvents = ["keydown", "pointerdown", "pointerup"];

        const setColWidth = (ths, tds, totalWidth) => {
            // Calculate the sum of fixed column widths
            const totalFixedWidth = FIXED_WIDTHS.reduce((a, b) => a + b, 0);
            // Calculate the available width of a variable column
            const variableWidth = totalWidth - totalFixedWidth;

            // Calculate the total proportion of non-fixed columns
            const totalVariableProportion = columnProportions.reduce((sum, prop, i) =>
                fixedCols.includes(i) ? sum : sum + prop, 0);

            ths.forEach((th, i) => {
                let w;
                if (fixedCols.includes(i)) {
                    w = FIXED_WIDTHS[fixedCols.indexOf(i)];
                } else {
                    // Allocate width to the variable column based on its proportions
                    w = Math.floor(variableWidth * (columnProportions[i] / totalVariableProportion));
                }
                th.style.width = `${w}px`;
                th.style.minWidth = `${w}px`;
                th.style.maxWidth = `${w}px`;
                th.style.overflow = "hidden";
                th.style.textOverflow = "ellipsis";
            });

            tds.forEach((td, i) => {
                const colIndex = i % ths.length;
                let w;
                if (fixedCols.includes(colIndex)) {
                    w = FIXED_WIDTHS[fixedCols.indexOf(colIndex)];
                } else {
                    w = Math.floor(variableWidth * (columnProportions[colIndex] / totalVariableProportion));
                }
                td.style.width = `${w}px`;
                td.style.minWidth = `${w}px`;
                td.style.maxWidth = `${w}px`;
                td.style.overflow = "hidden";
                td.style.textOverflow = "ellipsis";
            });
        };
        const startReSize = (ev) => {
            ev.preventDefault();
            ev.stopPropagation();

            const delta = ev.clientX - initialX;
            const leftNewWidth = Math.max(10, leftWidth + delta);
            const rightNewWidth = Math.max(10, rightWidth - delta);

            left.style.width = `${Math.floor(leftNewWidth)}px`;
            right.style.width = `${Math.floor(rightNewWidth)}px`;

            if (leftTable) {
                leftTable.style.width = `${Math.floor(leftNewWidth)}px`;
                setColWidth(Array.from(leftThElements), Array.from(leftTdElements), leftNewWidth);
            }
        };

        const stopReSize = (ev) => {
            if (ev.type === "pointerdown" && ev.button === 0) return;
            ev.preventDefault();
            ev.stopPropagation();

            window.removeEventListener("pointermove", startReSize);
            for (const eventType of resizeStoppingEvents) {
                window.removeEventListener(eventType, stopReSize);
            }

            /** Reset the left column width to maintain the original ratio **/
            if (leftTable && leftThElements.length > 0) {
                const newLeftWidth = left.getBoundingClientRect().width;
                leftTable.style.width = `${Math.floor(newLeftWidth)}px`;
                setColWidth(Array.from(leftThElements), Array.from(leftTdElements), newLeftWidth);
            }

            document.activeElement.blur();
        };

        window.addEventListener("pointermove", startReSize);
        for (const eventType of resizeStoppingEvents) {
            window.addEventListener(eventType, stopReSize);
        }
    }


    onRecordChanged(record, change) {
        this.treeFrom.isFormDirty = true;
        this.props.onFormChange(record, change);
    }

    async onCellClicked(record, column, ev) {
        if (this.treeFrom.current_record && this.treeFrom.selectedAction != 'SEQUENTIAL_EDIT') {
            this.props.onClickSave();
        }
        const records = await this.props.list.model._loadRecords(
            {
                resModel: this.props.list.resModel,
                resIds: [record.resId],
                activeFields: this.treeFrom.activeFields,
                fields: this.treeFrom.fields,
                context: this.props.list.context
            }
        );
        const model = this.props.list.model;
        model.hooks.onRecordChanged = this.onRecordChanged.bind(this);
        this.treeFrom.current_record = new Record(model, {
            ...this.props.list.model.config,
            mode: 'edit',
            isMonoRecord: true,
            resId: record.resId,
            resIds: [record.resId],
            resModel: this.props.list.resModel,
            activeFields: this.treeFrom.activeFields,
            fields: this.treeFrom.fields,
            context: this.props.list.context,
        }, records[0]);
        this.treeFrom.isFormDirty = false;
        this.props.openRecord(this.treeFrom.current_record)
    }

    getRowClass(record) {
        let result = super.getRowClass(record);
        if (this.treeFrom.current_record && record.resId === this.treeFrom.current_record.resId) {
            result += ' active';
        }
        return result
    }

    async BulkActionCheckOpened() {
        const isOpen = await new Promise((resolve) => {
            TreeFormControllerBus.trigger("GET_BULK_STATE", {resolve});
        });
        this.treeFrom.bulkAction = isOpen;
    }

    get canSelectRecord() {
        this.BulkActionCheckOpened();
        if (this.treeFrom.bulkAction) {
            return false;
        }
        return super.canSelectRecord;
    }
}

TreeFormRenderer.template = "odoopim_split_widget.TreeFormRenderer";
TreeFormRenderer.components = {
    ...ListRenderer.components,
    FormRenderer,
    ActionController,
    Filters,
}
TreeFormRenderer.props.push('onFormChange?');
TreeFormRenderer.props.push('onClickSave?');
