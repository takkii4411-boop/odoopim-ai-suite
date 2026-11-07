/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";


export class ProductKanbanRecord extends KanbanRecord {
    /*
    * Re-write to add its own classes for selected kanban record
    */
    getRecordClasses() {
        let result = super.getRecordClasses();
        if (this.props.record.selected) { result += " jstr-kanban-selected" };
        return result;
    }
    /*
    * The method to manage clicks on kanban record
    */
    onGlobalClick(ev) {
        if (ev.target.closest(".o_kanban_image")) {
            // An image is clicked --> standard open record action
            const { openRecord, record } = this.props;
            openRecord(record);
        }
        else {
            // Others clicks --> add to selection/remove from selection
            this.props.record.onRecordClick(ev, {});
        }
    }
};
