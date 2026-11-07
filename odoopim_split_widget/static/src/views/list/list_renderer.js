/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {ListRenderer} from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, {
    setup() {
        if (this.props.archInfo.editable){
            this.props.archInfo.editable = 'top';
        }
        super.setup();
        this.numSwitch = this.constructor.name === 'ListRenderer';
    },

    freezeColumnWidths() {
        super.freezeColumnWidths();
        const table = this.tableRef.el;
        const th = table.querySelector("thead .list-number");
        if (th) {
            const width = String(this.props.list.offset + this.props.list.limit).length * 10 + 20 + 'px';
            th.style.width = width;
            th.style.maxWidth = width;
        }
    }
})