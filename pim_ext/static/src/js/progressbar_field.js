/** @odoo-module **/

import { registry } from "@web/core/registry";
import { progressBarField, ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";

export class ProgressBarFieldExtended extends ProgressBarField {
    static template = "pim_ext.ProgressBarFieldInherit";
    get progressBarColorClass() {
    console.log("color",this.currentValue, this.maxValue);
        if (this.currentValue > this.maxValue) {
            return super.progressBarColorClass;
        }
        if (this.currentValue>=70){
        return "green_bar";
        }
        if (this.currentValue>=55 && this.currentValue<70){
        return "light_green_bar";
        }
        if (this.currentValue>=40 && this.currentValue<55){
        return "yellow_bar";
        }
        if (this.currentValue>=25 && this.currentValue<40){
        return "orange_bar";
        }
        if (this.currentValue>=0 && this.currentValue<25){
        return "red_bar";
        }

    }
}

export const ProgressBarFieldExtendedWidget = {
    ...progressBarField,
    component: ProgressBarFieldExtended,
};

registry.category("fields").add("progressbar_extended", ProgressBarFieldExtendedWidget);
