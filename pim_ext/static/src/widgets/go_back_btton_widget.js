/* @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useRecordObserver } from "@web/model/relational_model/utils";

import { Component, useState, onWillStart } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";


export class GoBackComponent extends Component {
    static template = "pim_ext.GoHistoryBackComponent";
    static props = { ...standardWidgetProps };

    setup() {

    }
    onClick() {
        window.history.back();
    }
}

export const goBackComponent = {
    component: GoBackComponent,
};
registry.category("view_widgets").add("back_button", goBackComponent);
