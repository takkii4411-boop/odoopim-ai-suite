/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {IntegerField} from "@web/views/fields/integer/integer_field";
import {formatInteger} from "@web/views/fields/formatters";
import {registry} from "@web/core/registry";

patch(IntegerField.prototype, {
    get formattedValue() {
        if (
            !this.props.formatNumber ||
            (!this.props.readonly && this.props.inputType === "number")
        ) {
            return this.value;
        }
        if (this.props.humanReadable && !this.state.hasFocus) {
            return formatInteger(this.value, {
                humanReadable: true,
                decimals: this.props.decimals,
            });
        } else {
            return formatInteger(this.value, {humanReadable: false});
        }
    }
})

export function formatIntegerExtend(value, options = {}) {
    if (!value) return 0;
    return formatInteger(value, {humanReadable: false})
}

registry.category("formatters").add("integer", formatIntegerExtend, {force: true})