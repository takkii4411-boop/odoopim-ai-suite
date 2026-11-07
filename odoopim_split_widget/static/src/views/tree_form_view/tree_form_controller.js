/** @odoo-module */

import {ListController} from "@web/views/list/list_controller";
import {executeButtonCallback} from "@web/views/view_button/view_button_hook";
import { download } from "@web/core/network/download";
import { useState, EventBus } from "@odoo/owl";

export const TreeFormControllerBus = new EventBus();

export class TreeFormController extends ListController {
    setup() {
        super.setup();
        this.myState = useState({
            isFilterOpened: false,
            isBulkActionOpened: false,
        });
        this.isFormChange = false;
        this.editedRecord = null;
        this.props.Renderer.defaultProps = {...this.props.Renderer.defaultProps, controllerRef: this}
        TreeFormControllerBus.addEventListener("CLOSE_ACTIONS", this.closeActions.bind(this));
        TreeFormControllerBus.addEventListener("BULK_ACTION_OPEN", this.openBulkActions.bind(this));
        TreeFormControllerBus.addEventListener("GET_BULK_STATE", (ev) => {
            ev.detail.resolve(this.myState.isBulkActionOpened);
        });
    }
    getBulkOpened(){
        return this.myState.isBulkActionOpened;
    }
    openBulkActions(){
        this.myState.isBulkActionOpened = true;
    }
    toggleFilter(){
        this.myState.isFilterOpened = !this.myState.isFilterOpened;
        if(this.myState.isFilterOpened){
            this.setLeftRightWidth(80,20);
        }else{
            this.setLeftRightWidth(100,0);
        }
    }

    async onClickDiscard() {
        return executeButtonCallback(this.rootRef.el, async () => {
                let editedRecord = this.editedRecord;
                if (!editedRecord) editedRecord = this.myState.editedRecord;

                this.isFormChange = false;
                await editedRecord.discard();
                await editedRecord.load();
                this.render();
            }
        );
    }

    async onClickSave() {
        if (!this.isFormChange)return ;
        return executeButtonCallback(this.rootRef.el, async () => {
            let editedRecord = this.editedRecord;
            if (!editedRecord) editedRecord = this.myState.editedRecord;

            const saved = await editedRecord.save();
            if (saved) {
                await editedRecord.load();
                await this.model.load();
                this.isFormChange = false;
                this.render();
            }
        });
    }

    async openRecord(record) {
        this.closeActions();
        this.editedRecord = record;
        this.myState.editedRecord = record;
        this.setLeftRightWidth(60,40);
    }
    closeActions(){
        if(this.myState.isFilterOpened){
            this.toggleFilter();
        }
        this.myState.isBulkActionOpened = false;
    }
    setLeftRightWidth(left, right) {
        document.getElementsByClassName('tree-form-tree')[0].style.width = left + '%';
        document.getElementsByClassName('tree-form-form')[0].style.width = right + '%';
    }

    onFormChange(record, change) {
        this.isFormChange = true;
        this.myState.editedRecord = record;
        this.render();
    }

    async onClickExport(e){
        await download({
            data: {
                data: JSON.stringify({
                    model: this.env.config.getDisplayName(),
                    resModel: this.props.resModel,
                    domain: this.env.searchModel.domain,
                    context: this.props.context
                }),
            },
            url: `/web/export/xls_view_tree_form`,
        });
    }
}

TreeFormController.template = 'odoopim_split_widget.TreeFormView';
