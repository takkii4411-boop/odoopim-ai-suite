/** @odoo-module **/

import {FloatField, floatField} from "@web/views/fields/float/float_field";
import {registry} from "@web/core/registry";
import {formatFloat} from "@web/core/utils/numbers";

export class OdooPimNullFloat extends FloatField {
    get formattedValue() {
        const val = this.props.record.data[this.props.name + '_char'];
        console.log(val);
        if(val && this.value == 0){
            return 0
        }else if (!val && this.value == 0){
            return ''
        }
        if (this.value && Number.isInteger(this.value)) {
            return Number(this.value);
        } else {
            return formatFloat(this.value);
        }
    }
}

export const odoopimNullFloat = {
    ...floatField,
    component: OdooPimNullFloat,
};
registry.category("fields").add("odoopim_null_float", odoopimNullFloat);