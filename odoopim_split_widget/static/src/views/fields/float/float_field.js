/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {FloatField} from "@web/views/fields/float/float_field";
import {registry} from "@web/core/registry";
import {formatFloat} from "@web/core/utils/numbers";


patch(FloatField.prototype, {
    get formattedValue() {
        if (!this.value) return '';
        if (this.value && Number.isInteger(this.value)) {
            return Number(this.value);
        } else {
            if (
                !this.props.formatNumber ||
                (this.props.inputType === "number" && !this.props.readonly && this.value)
            ) {
                return this.value;
            }
            if (this.props.humanReadable && !this.state.hasFocus) {
                return formatFloat(this.value, {
                    digits: this.digits,
                    humanReadable: true,
                    decimals: this.props.decimals,
                });
            } else {
                return formatFloat(this.value, {digits: this.digits, humanReadable: false});
            }
        }
    }
})


export function formatFloatExtend(value, options = {}) {
    if (!value) return 0;
    if (value && Number.isInteger(value)) {
        return Number(value);
    } else {
        return formatFloat(value);
    }
}

registry.category("formatters").add("float", formatFloatExtend, {force: true})