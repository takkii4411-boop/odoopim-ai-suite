/** @odoo-module **/

import { localization } from "@web/core/l10n/localization";
import { user } from "@web/core/user";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
import { TranslationLocaleDialog } from "@pim_locales_channels/channel_dialouge/channel_dialog"
import { _t } from "@web/core/l10n/translation";


export class ChannelTranslationButton extends Component {
    static template = "pim_locales_channels.ChannelTranslationButton";
    static props = {
        fieldName: { type: String },
        record: { type: Object },
    };
    setup() {
        this.orm = useService("orm");
        this.addDialog = useOwnedDialogs();
    }
    onClick() {
        this.addDialog(TranslationLocaleDialog, {
            fieldName: this.props.fieldName,
            record: this.props.record,
            title: _t("Channelization X Localisation"),
        });
    }
    get isTranslate(){
        return true;
    }
}
