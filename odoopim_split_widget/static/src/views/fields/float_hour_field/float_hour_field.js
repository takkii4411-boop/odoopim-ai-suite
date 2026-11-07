/** @odoo-module **/

import {Component, xml} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useInputField} from "@web/views/fields/input_field_hook";
import {useNumpadDecimal} from "@web/views/fields/numpad_decimal_hook";


export class FloatHourField extends Component {

    setup() {
        useInputField({
            getValue: () => this.formattedValue,
            refName: "numpadDecimal",
            parse: (v) => this.parse(v),
        });
        useNumpadDecimal();
    }

    parse(v) {
        try {
            let val = Number(v.trim());
            if (val < 0) return undefined;
            let hours = Math.floor(val);
            let minutes = Math.round((val - hours) * 100);
            if (minutes === 60) {
                val = hours += 1;
                minutes = 0;
            }
            if (minutes > 60 || hours >= 24) return undefined;
            if (hours < 24) return val;
        } catch {
        }
        return undefined;
    }

    get formattedValue() {
        const val = this.props.record.data[this.props.name];
        if (!val) return "00:00";
        const hours = Math.floor(val);
        const minutes = Math.round((val - hours) * 100);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    }
}

FloatHourField.props = {
    ...standardFieldProps,
    inputType: {type: String, optional: true},
}
FloatHourField.defaultProps = {
    inputType: 'text'
}
FloatHourField.template = xml`<t><span t-if="props.readonly" t-esc="formattedValue"/><input t-else="" t-att-id="props.id" t-att-type="props.inputType" t-ref="numpadDecimal" class="o_input" autocomplete="off" /></t>`;

export const floatHourField = {
    component: FloatHourField,
    supportedTypes: ["float"],
}

registry.category("fields").add("float_hour", floatHourField);
