/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useState, Component, useEffect } from "@odoo/owl";

class PimColor extends Component {
    static template = "pim_ext.PimColor";
    static props = { ...standardFieldProps };
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            selections : [],
            color: this.field_value || "",
            show_colors: false
        });
        this.get_field_values();
        useEffect(() => {
            this.reset_state();
        }, () => [this.props.record.data.id]);
    }
    ClickOpenColors(){
        this.state.show_colors = true;
    }
    reset_state(){
        this.get_field_values();
        this.state.color = this.field_value || "";
        this.state.show_colors = false;
    }
    async get_field_values() {
        try {
            const [fields] = await this.orm.searchRead(
                "ir.model.fields",
                [["name", "=", this.props.name], ["model", "=", this.props.record.resModel]],
                ["id", "selection_ids"]
            );
            if (!fields) {
                console.warn(`No field found for ${this.props.name}`);
                this.state.selections = [];
                return;
            }
            const selections = await this.orm.searchRead(
                "ir.model.fields.selection",
                [["id", "in", fields.selection_ids]],
                ["id", "value", "name"]
            );
            this.state.selections = selections;
        } catch (error) {
            console.error("Error while fetching field values:", error);
            this.state.selections = [];
        }
    }
    get field_value(){
        return this.props.record.data[this.props.name];
    }
    async switchColor(value) {
        this.props.record.update({ [this.props.name]: value });
        this.state.show_colors = false;
        this.state.color = value;
    }
}

registry.category("fields").add("pim_color", {
    component: PimColor,
});
