/** @odoo-module **/
import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { RightPanel } from "./family_rightpanel";
import { Component, EventBus, onWillStart, useSubEnv, useState,onMounted } from "@odoo/owl";
import { ProductNavigation } from "./family_navigation";
import {FamilySearchModel } from "./family_search_model";
import { Domain } from "@web/core/domain";

import { DynamicRecordList } from "@web/model/relational_model/dynamic_record_list";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { Record } from "@web/model/relational_model/record";
var custom_discontinued = false;
export class FamilyKanbanDynamicRecordList extends DynamicRecordList {
    /*
    * Re-write to trigger toggle selection for the old selection
    */
    setup(config, data) {
        super.setup(...arguments);
        this.reSelect();
    }
    /*
    * Re-write to trigger toggle selection for the old selection
    */
    async _load(offset, limit, orderBy, domain) {
        await super._load(...arguments);
        this.reSelect();
    }
    /*
    * The method to trigger toggle selection for the old selection
    */
    reSelect() {
        if (this.records.length) {
            const selectedRecords = this.model.selectedRecords;
            this.records.forEach(function (record) {
                if (selectedRecords.find(rec => rec.id === record.resId)) {
                    record.selected = true;
                };
            });
        };
    }
}

export class FamilyRecord extends Record {
    /**
    * The method to manage kanban records clicks: to add an item to selection
    */
    onRecordClick(ev, options = {}) {
        this.toggleSelection(!this.selected);
    }
    /*
    * Overwrite to save selection for model, not only in a record. The idea is to not update selection after each reload
    */
    toggleSelection(selected) {
        super.toggleSelection(selected);
        this.model._updateModelSelection({"id": this.resId, "name": this.data.name}, selected);
    }
};

export class FamilyKanbanModel extends RelationalModel {
    static Record = FamilyRecord;
    static DynamicRecordList = FamilyKanbanDynamicRecordList;
    /*
    * Re-write to introduce selected records, so our list will be restored from previous selection (if any)
    */
    setup(params, { action, company, dialog, notification, rpc, user }) {
        if (params.state) {
            this.selectedRecords = params.state.selectedRecords || [];
        }
        else {
            this.selectedRecords = [];
        }
        super.setup(...arguments);
    }
    /*
    * The method to add/remove record from SelectedRecords
    */
    _updateModelSelection(record, selected) {
        if (selected) {
            this.selectedRecords.push(record)
        }
        else {
            this.selectedRecords = this.selectedRecords.filter(rec => rec.id != record.id)
        };
    }
    /*
    * Overwrite to save selected records to state
    */
    exportState() {
        const state = {
            ...super.exportState(),
            selectedRecords: this.selectedRecords,
        };
        return state
    }
};

export class FamilyKanbanRecord extends KanbanRecord {
    getRecordClasses() {
        let result = super.getRecordClasses();
        if (this.props.record.selected) { result += " jstr-kanban-selected" };
        return result;
    }
    /*
    * The method to manage clicks on kanban record
    */
    onGlobalClick(ev) {
        if (ev.target.closest(".o_kanban_record_title")) {
        this.props.record.onRecordClick(ev, {});
        }
        else {
             return super.onGlobalClick(...arguments);
        }
    }
}

export class FamilyKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
        this.action = useService("action");
    }
    getFamilyManagerProps() {
        return {
            currentSelection: this.props.list.selection || [],
            selection: this.props.list.model.selectedRecords || [],
            model: this.props.list.model,
            archInfo : this.props.archInfo,
            optionalActiveFields : this.props.list.optionalActiveFields || {},
            fields: this.fields || {}
        };
    }
    getProductNavigationProps() {
        return {
            kanbanList: this.props.list,
        }
    }

}
FamilyKanbanRenderer.template = "FamilyKanbanRenderer";
FamilyKanbanRenderer.components = Object.assign({}, KanbanRenderer.components, {
    RightPanel,
    ProductNavigation,
    KanbanRecord: FamilyKanbanRecord,
});

export class RightPanelKanbanController extends KanbanController {
    static template = "RightPanelKanbanController";

    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.orderId = this.props.context.order_id;
        this.orderResModel = this.props.context.product_catalog_order_model;
         this.show_discontinued = custom_discontinued ;
         onMounted(() => {
                    console.log("custom_discontinued",custom_discontinued);
                    if (custom_discontinued){
                        this.showarchived();
                    }
//                    else{
//                        this.hidearchived();
//                    }

                })
    }


            showarchived() {
                custom_discontinued = true;
                this.show_discontinued = true;
                var domain = [['active', 'in', [true,false]]];
                this.env.searchModel.discontinued_domain = domain;
                this.env.searchModel.PushDiscontinuedDomain();
           }
           hidearchived() {
                custom_discontinued = false;
                this.show_discontinued = false;
                var domain = [];
                this.env.searchModel.discontinued_domain = domain;
                 this.env.searchModel.PushDiscontinuedDomain();
           }


    get canCreate() {
        return true;
    }
}

export const FamilyKanbanView = {
    ...kanbanView,
    SearchModel: FamilySearchModel,
    Controller: RightPanelKanbanController,
    Renderer: FamilyKanbanRenderer,
    Model: FamilyKanbanModel,
};

registry.category("views").add("family_kanban_panel", FamilyKanbanView);
