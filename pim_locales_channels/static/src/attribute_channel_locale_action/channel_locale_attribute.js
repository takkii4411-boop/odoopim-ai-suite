/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";
import { loadLanguages } from "@web/core/l10n/translation";
import { onWillStart, useState } from "@odoo/owl";
import { FieldsEditPopup } from "@pim_locales_channels/field_edit/fields_edit";

export class AttributeChannelLocalePop extends Component {
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        datas: Object,
        resModel: String,
        resId: Number,
        close: Function,
    };
    static template = "pim_locales_channels.AttributeChannelLocalePop";
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.addDialog = useOwnedDialogs();
        this.state = useState({
            datas: this.props.datas,
            changes: {},
            grouped : false
        });
    }
    onValueChange(ev) {
        const val = ev.target.value;

        const fieldName = ev.target.dataset.field;
        const fieldId = parseInt(ev.target.dataset.fieldId);
        const langId = parseInt(ev.target.dataset.langId);
        const platform = ev.target.dataset.platform;

        const platformRows = this.state.datas[platform];
        const row = platformRows.find(r => r.x_field_name === fieldName);

        if (row && row.langs[langId]) {
            row.langs[langId].x_value = val;
        }

        if (!this.state.changes[platform]) {
            this.state.changes[platform] = [];
        }

        const existing = this.state.changes[platform].find(
            c => c.x_field_name === fieldName && c.x_lang_id === langId
        );

        if (existing) {
            existing.x_value = val;
        } else {
            this.state.changes[platform].push({
                x_res_id: this.props.resId,
                x_res_model: this.props.resModel,
                x_field_name: fieldName,
                x_lang_id: langId,
                x_value: val,
            });
        }
    }
    async onSave() {
        const vals = this.state.changes
        if (Object.keys(vals).length === 0) {
            this.props.close();
            return;
        }
        await this.orm.call(
            this.props.resModel,
            "update_field_channel_and_locale",
            [
                this.props.resId,
                vals
            ]
        );
        this.props.close();
    }
    groupByType() {
        const grouped = {};

        for (const platform in this.state.datas) {
            const rows = this.state.datas[platform];

            const typeGroups = {};

            for (const row of rows) {
                const ttype = row.ttype || "unknown";

                if (!typeGroups[ttype]) {
                    typeGroups[ttype] = [];
                }
                typeGroups[ttype].push(row);
            }

            grouped[platform] = typeGroups;
        }
        this.state.grouped = true;
        this.state.datas = grouped;
    }
    ungroupByType(){
        this.state.grouped = false;
        this.state.datas = this.props.datas;
    }

    EnableTranslationFields(){
        this.addDialog(FieldsEditPopup, {
            fields: ['name'],
            resModel: this.props.resModel,
            title: "Enable Fields for Translation",
        });
    }

    get is_multiLingual(){
        return this.props.datas.includes('global');
    }
    get isNoVals() {
        return Object.keys(this.props.datas).length ? true : false;
    }
}

export function AttributeChannelLocaleAction(env, action) {
    const params = action.params || {};
    const props = {
        title: params.title || "Channel Locale Update",
        datas: params.datas || [],
        resModel: params.resModel,
        resId: params.resId,
        title: params.title,
    };
    const dialog = env.services.dialog;
    dialog.add(AttributeChannelLocalePop, props);
    return params.next;
}

registry.category("actions").add("attr_channel_locale_update", AttributeChannelLocaleAction);
