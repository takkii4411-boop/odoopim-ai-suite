/** @odoo-module **/

import { registry } from "@web/core/registry";
import { blockDom, Component, useState, useRef } from "@odoo/owl";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { computeViewClassName } from "@web/views/utils";
import { _t } from "@web/core/l10n/translation";
import {
    useActiveActions,
    useAddInlineRecord,
    useOpenX2ManyRecord,
    useSelectCreate,
    useX2ManyCrud,
} from "@web/views/fields/relational_utils";

patch(X2ManyField.prototype, {
    setup(){
        this.MultiState = useState({
            currentView: this.props.viewMode || "list",
        });
        super.setup(...arguments);
        console.log()

    },
    switchView(viewType) {
        this.MultiState.currentView = viewType;
        this.field = this.props.record.fields[this.props.name];
        const { saveRecord, updateRecord, removeRecord } = useX2ManyCrud(
            () => this.list,
            this.isMany2Many
        );
        this.archInfo = this.props.views?.[viewType] || {};
        const classes = viewType
            ? ["o_field_x2many", `o_field_x2many_${viewType}`]
            : ["o_field_x2many"];
        this.className = computeViewClassName(viewType, this.archInfo.xmlDoc, classes);

        const { activeActions, creates } = this.archInfo;
        if (viewType === "kanban") {
            this.creates = creates.length
                ? creates
                : [
                      {
                          type: "create",
                          string: this.props.addLabel || _t("Add"),
                          class: "o-kanban-button-new",
                      },
                  ];
        }
        this.canOpenRecord =
            viewType === "list"
                ? !(this.archInfo.editable || this.props.editable)
                : true;
    },
    get activeField() {
        return {
            fields: this.props.relatedFields,
            views: this.props.views,
            viewMode: this.MultiState.currentView,
            string: this.props.string,
        };
    },
    get displayControlPanelButtons() {
        return (
            this.MultiState.currentView === "kanban" &&
            ("link" in this.activeActions ? this.activeActions.link : this.activeActions.create) &&
            !this.props.readonly
        );
    },
    get rendererProps() {
        const { archInfo } = this;
        const props = {
            archInfo,
            list: this.list,
            openRecord: this.openRecord.bind(this),
        };

        if (this.MultiState.currentView === "kanban") {
            const recordsDraggable = !this.props.readonly && archInfo.recordsDraggable;
            props.archInfo = { ...archInfo, recordsDraggable };
            props.readonly = this.props.readonly;
            // TODO: apply same logic in the list case
            props.deleteRecord = (record) => {
                if (this.isMany2Many) {
                    return this.list.forget(record);
                }
                return this.list.delete(record);
            };
            return props;
        }

        const editable =
            (this.archInfo.activeActions.edit && archInfo.editable) || this.props.editable;
        props.activeActions = this.activeActions;
        props.cycleOnTab = false;
        props.editable = !this.props.readonly && editable;
        props.nestedKeyOptionalFieldsData = this.nestedKeyOptionalFieldsData;
        props.onAdd = (params) => {
            params.editable =
                !this.props.readonly && ("editable" in params ? params.editable : editable);
            this.onAdd(params);
        };
        props.onOpenFormView = this.switchToForm.bind(this);
        props.hasOpenFormViewButton = archInfo.editable ? archInfo.openFormView : false;
        return props;
    },
    get is_multi_view() {
        return String(this.props.context?.multi_view).toLowerCase() === "true";
    }
});
