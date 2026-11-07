/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class FieldProgress extends Component {

    get displayValue() {
        const val = this.props.record.data[this.props.name] || 0;
        return Math.round(val) + "%";   // rounds to nearest integer
    }

    get progressWidth() {
        return (this.props.record.data[this.props.name] || 0) + "%";
    }

    get getBgClass() {
        let percentage = this.props.record.data[this.props.name] || 0;
        if (percentage >= 70) {
            return "oe_green_bg";
        } else if (percentage >= 55 && percentage < 70) {
            return "oe_light_green_bg";
        } else if (percentage >= 40 && percentage < 55) {
            return "oe_yellow_bg";
        } else if (percentage >= 25 && percentage < 40) {
            return "oe_orange_bg";
        } else if (percentage >= 0 && percentage < 25) {
            return "oe_red_bg";
        } else {
            return ""; // default or invalid value
        }
    }

}

FieldProgress.template = "my_module.FieldProgress";
FieldProgress.props = {
    ...standardFieldProps,
};
FieldProgress.supportedTypes = ["integer", "float"];

registry.category("fields").add("field_progress", {
    component: FieldProgress,
    supportedTypes: ["integer", "float"],
});
