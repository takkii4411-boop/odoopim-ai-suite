/** @odoo-module **/
/**
 * Boolean Radio Widget with Custom Labels & Help Text
 * =====================================================
 *
 * Replaces the default boolean toggle/checkbox with beautiful Yes/No radio buttons.
 *
 * Features:
 * - Horizontal or vertical layout
 * - Fully customizable Yes/No labels
 * - Optional helper text displayed below the radios (different for True/False)
 * - Custom CSS classes for helper text (e.g. text-success, text-danger)
 * - Works in form, list (with autosave), and kanban views
 * - Full readonly support
 *
 * Usage in views:
 * ----------------
 * <field name="is_mandatory" widget="boolean_radio"/>
 *
 * Full example with all options:
 * ------------------------------
 * <field name="is_mandatory"
 *        widget="boolean_radio"
 *        options="{
 *            'layout': 'horizontal',                    <!-- or 'vertical' -->
 *            'true_label': 'Mandatory',
 *            'false_label': 'Optional',
 *            'true_text': 'Yes its mandatory',
 *            'true_text_class': 'text-success fw-bold',
 *            'false_text': 'Make it Mandatory',
 *            'false_text_class': 'text-danger',
 *            'autosave': true                           <!-- useful in tree views -->
 *        }"/>
 *
 * Supported options (all optional):
 * ---------------------------------
 * layout             : 'horizontal' | 'vertical'       (default: horizontal)
 * true_label         : Text for "Yes" radio            (default: Yes)
 * false_label        : Text for "No" radio             (default: No)
 * true_text          : Helper text shown when True     (default: empty)
 * false_text         : Helper text shown when False    (default: empty)
 * true_text_class    : CSS classes for true helper     (default: text-info)
 * false_text_class   : CSS classes for false helper    (default: text-info)
 * autosave           : Save immediately on change      (default: false)
 *
 * Author: ANAND MC || anand.mc.ofcl@gmail.com
 * Compatible: Odoo 18.0+
 */
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { booleanField, BooleanField } from "@web/views/fields/boolean/boolean_field";

export class BooleanRadioField extends BooleanField {
    static props = {
        ...BooleanField.props,
        autosave: { type: Boolean, optional: true },
        layout: { type: String, optional: true },
        true_label: {type: String, optional: true },
        false_label: {type: String, optional: true },
        true_text: {type: String, optional: true },
        false_text: {type: String, optional: true },
        true_text_class: {type: String, optional:true },
        false_text_class: {type: String, optional:true }
    };
    static template = "pim_ext.BooleanRadioFieldTemplate";

    setup(){
        super.setup(...arguments);
        this.state.value = this.props.record.data[this.props.name];
        console.log(this)
    }

    get isVertical() {
        return this.props.layout === "vertical";
    }

    async onChange(value) {
        this.state.value = value;
        console.log(value)
        const changes = { [this.props.name]: value };
        await this.props.record.update(changes, { save: this.props.autosave });
    }

    get value(){
        return this.props.record.data[this.props.name];
    }
}

export const booleanRadioField = {
    component: BooleanRadioField,
    supportedOptions: [
        {
            label: "Layout", name: "layout", type: "string",
            help: "Use 'horizontal' or 'vertical'",  default: "horizontal",
        },
        {
            label: "True Label", name: "true_label", type: "string",
            help: "specify label when select true", default: "yes",
        },
        {
            label: "False Label", name: "false_label", type: "string",
            help: "specify label when select false", default: "No",
        },
        {
            label: "True Text", name: "true_text", type: "string",
            help: "Show some text under the field when true", default: "",
        },
        {
            label: "False Text", name: "false_text", type: "string",
            help: "Show some text under the field when false", default: "",
        },
        {
            label: "True Text Class", name: "true_text_class", type: "string",
            help: "Add class to the true help text", default: "text-info",
        },
        {
            label: "False Text Class", name: "false_text_class", type: "string",
            help: "Add class to the false help text", default: "text-info",
        },
        {
            label: "Autosave", name: "autosave", type: "boolean",
        },
    ],
    extractProps: (fieldInfo, dynamicInfo) => ({
        layout: fieldInfo.options?.layout,
        true_label: fieldInfo.options?.true_label || 'Yes',
        false_label: fieldInfo.options?.false_label || 'No',
        true_text: fieldInfo.options?.true_text || '',
        false_text: fieldInfo.options?.false_text || '',
        true_text_class: fieldInfo.options?.true_text_class || 'text-info',
        false_text_class: fieldInfo.options?.false_text_class || 'text-info',
    }),
};

registry.category("fields").add("boolean_radio", booleanRadioField);
