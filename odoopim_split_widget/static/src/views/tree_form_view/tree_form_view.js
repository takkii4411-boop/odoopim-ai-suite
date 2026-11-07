/** @odoo-module */

import {registry} from "@web/core/registry";
import {listView} from "@web/views/list/list_view";
import {TreeFormRenderer} from "./tree_form_renderer";
import {TreeFormController} from "./tree_form_controller";

export const treeFormView = {
    ...listView,
    Renderer: TreeFormRenderer,
    Controller: TreeFormController,
    buttonTemplate: "odoopim_split_widget.TreeFormView.Buttons",

    props: (genericProps, view) => {
        const {ArchParser} = view;
        const {arch, relatedModels, resModel} = genericProps;
        const archInfo = new ArchParser().parse(arch, relatedModels, resModel);

        return {
            ...genericProps,
            className: genericProps.className + ' o_form_view',
            Model: view.Model,
            Renderer: view.Renderer,
            buttonTemplate: view.buttonTemplate,
            archInfo,
        };
    },
}

registry.category("views").add("tree_form_view", treeFormView);