/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class FieldBorder extends Component {}

FieldBorder.template = "odoopim_split_widget.FieldBorder";
FieldBorder.props = {
    ...standardFieldProps,
};

// Register properly with component key
registry.category("fields").add("field_border", {
    component: FieldBorder,
    supportedTypes: ["char"], // pick types you want
});
