/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";
import { loadLanguages } from "@web/core/l10n/translation";
import { onWillStart, useState } from "@odoo/owl";
import { FieldsEditPopup } from "@pim_locales_channels/field_edit/fields_edit";
import { ProductVariantCreation } from "@pim_ext/widgets/varaint_creation/product_variant";


export class VariantCreation extends Component {
    static components = { Dialog, ProductVariantCreation };
    static props = {
        title: { type: String, optional: true },
        name : String,
        resModel: String,
        resId: Number,
        close: Function,
    };
    static template = "pim_ext.VariantCreation";
    setup() {
        super.setup();
        this.orm = useService("orm");
    }
}


export function VariantCreationAction(env, action) {
    const params = action.params || {};
    const props = {
        title: params.title || "Create Variants",
        resModel: params.resModel,
        resId: params.resId,
        name: params.name,
    };
    const dialog = env.services.dialog;
    dialog.add(VariantCreation, props);
    return params.next;
}

registry.category("actions").add("variant_creation", VariantCreationAction);