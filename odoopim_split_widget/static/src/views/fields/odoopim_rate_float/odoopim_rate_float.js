/** @odoo-module **/

import {FloatField, floatField} from "@web/views/fields/float/float_field";
import {registry} from "@web/core/registry";
import {formatFloat} from "@web/core/utils/numbers";

export class OdooPimRateFloat extends FloatField {
    get formattedValue() {
        if (
            !this.props.formatNumber ||
            (this.props.inputType === "number" && !this.props.readonly && this.value)
        ) {
            return String(this.value)+'%';
        }
        if (this.props.humanReadable && !this.state.hasFocus) {
             let res = formatFloat(this.value, {
                digits: this.digits,
                humanReadable: true,
                decimals: this.props.decimals,
            });
            return String(res)+'%';
        } else {
            let res = formatFloat(this.value, { digits: this.digits, humanReadable: false });
            return String(res)+'%';
        }
    }
}

export const odoopimRateFloat = {
    ...floatField,
    component: OdooPimRateFloat,
};
registry.category("fields").add("odoopim_rate_float", odoopimRateFloat);