/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class TranslationLocaleDialog extends Component {
    static template = "pim_locales_channels.TranslationLocaleDialog";
    static components = { Dialog };
    static props = {
        record: { type: Object },
        fieldName: String,
        title: String,
        close: Function
    };
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            datas: {},
            changes: {}
        })
        onWillStart(async () => {
            await this.loadSavedValues();
        });
    }

    async loadSavedValues() {
        const { resModel, resId } = this.props.record;
        if (!resId || !this.props.fieldName) return;

        const vals = await this.orm.call(
            resModel,
            "prepare_channel_local_vals",
            [resId, [this.props.fieldName]]
        );
        this.state.datas = vals
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
        const vals = this.state.changes;
        if (Object.keys(vals).length === 0) {
            this.props.close();
            return;
        }
        await this.orm.call(
            this.props.record.resModel,
            "update_field_channel_and_locale",
            [
                this.props.record.resId,
                vals
            ]
        );
        this.props.close();
    }
}