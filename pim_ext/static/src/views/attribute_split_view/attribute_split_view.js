/** @odoo-module */
import {registry} from "@web/core/registry";
import {listView} from "@web/views/list/list_view";
import {AttributeSplitRenderer} from "./attribute_split_renderer";
import {AttributeSplitController} from "./attribute_split_controller";
export const attributeSplitView = {
    ...listView,
    Renderer: AttributeSplitRenderer,
    Controller: AttributeSplitController,
    buttonTemplate: "web.ListView.Buttons", // Use default button template
    props: (genericProps, view) => {
        const {ArchParser} = view;
        const {arch, relatedModels, resModel} = genericProps;
        const archInfo = new ArchParser().parse(arch, relatedModels, resModel);
        return {
            ...genericProps,
            className: (genericProps.className || "") + " o_pim_attribute_split_view",
            Model: view.Model,
            Renderer: view.Renderer,
            buttonTemplate: view.buttonTemplate,
            archInfo,
        };
    },
};
registry.category("views").add("pim_attribute_split_view", attributeSplitView);