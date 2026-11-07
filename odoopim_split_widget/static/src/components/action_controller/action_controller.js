/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import {BulkAction} from "../bulk_action/bulk_action";
import {EditCommonAttribute} from "../edit_common_attribute/edit_common_attribute";
import {EditAttribute} from "../edit_attribute/edit_attribute";
import { TreeFormControllerBus } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller"

export class ActionController extends Component{
    static template = "odoopim_split_widget.ActionController";
    static components = {BulkAction,EditCommonAttribute,EditAttribute};
    static props = {
        isFormChange: {type: Boolean, optional: true},
        renderer: {type: Object},
        parentAction: {type: String, optional: true},
    }

    setup() {
        super.setup();
        this.state = useState({
            selectedBulkAction: false,
            currentStep: 1,
        });
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.isFormChange = false;
    }

    goBack(){
        this.props.renderer.childBackCallback();
        TreeFormControllerBus.trigger('CLOSE_ACTIONS');
    }

    get actions(){
        return [
        {
            "label": "Add/Edit Attributes Values",
            "action": "EDIT_ATTRIBUTES_VALUES",
            "image_url": "/odoopim_split_widget/static/src/icons/edit-attributes.svg"
        },
        {
            "label": "Select family",
            "action": "CHANGE_FAMILY",
            "image_url": "/odoopim_split_widget/static/src/icons/change-family.svg",
            "attributes": ["family_id"]
        },
        {
            "label": "Select status",
            "action": "CHANGE_STATUS",
            "image_url": "/odoopim_split_widget/static/src/icons/change-status.svg",
            "attributes": ["active"]
        },
        {
            "label": "Select channels",
            "action": "PUBLISH_TO_CHANNEL",
            "image_url": "/odoopim_split_widget/static/src/icons/add-attribute.svg"
        },
        {
            "label": "Select groups",
            "action": "ADD_TO_GROUPS",
            "image_url": "/odoopim_split_widget/static/src/icons/add-to-group.svg"
        },
        {
            "label": "Select categories",
            "action": "ADD_TO_CATEGORIES",
            "image_url": "/odoopim_split_widget/static/src/icons/add-category.svg",
            "attributes": ["pim_category_ids"]
        },
        {
            "label": "Select source and target categories",
            "action": "MOVE_BETWEEN_CATEGORIES",
            "image_url": "/odoopim_split_widget/static/src/icons/move-between-category.svg"
        },
        {
            "label": "Configure AI enrichment",
            "action": "AI_ENRICHMENT",
            "image_url": "/odoopim_split_widget/static/src/icons/ai-enrichment.svg"
        },
        {
            "label": "Select product model",
            "action": "ADD_TO_AN_EXISTING_PRODUCT_MODEL",
            "image_url": "/odoopim_split_widget/static/src/icons/add-to-existing.svg"
        },
        {
            "label": "Select parent product model",
            "action": "CHANGE_THE_PARENT_PRODUCT_MODEL",
            "image_url": "/odoopim_split_widget/static/src/icons/change-parent.svg"
        },
        {
            "label": "Confirm conversion",
            "action": "CONVERT_TO_SIMPLE_PRODUCTS",
            "image_url": "/odoopim_split_widget/static/src/icons/convert-simple-product.svg"
        },
        {
            "label": "Associate",
            "action": "ASSOCIATE",
            "image_url": "/odoopim_split_widget/static/src/icons/associate.svg"
        }
    ];

    }
    getSelectedActionObject(){
        return this.actions.find(action => action.action === this.state.selectedBulkAction);
    }

    getStepLabel() {
        if (this.state.selectedBulkAction) {
            const selectedAction = this.getSelectedActionObject();
            return selectedAction?.label || "Edit values";
        }
        return "Edit values";
    }
    changeBulkAction(action){
        this.state.selectedBulkAction = action;
    }
    changeStep(step){
        let newStep = this.state.currentStep + step;
        if(newStep < 1 || newStep > 3){
            return;
        }
        if(this.state.currentStep === 1 && this.state.selectedBulkAction === false){
            this.notification.add("Select at least one action", {
                title: "No action selected",
                type: "danger",
            });
            return;
        }
        this.state.currentStep += step;
    }
    async saveChanges(attributeValues){
        try{
            let ids = [];
            for(const record of this.props.renderer.props.list.selection){
                ids.push(record.resId);
            }
            const response = await this.orm.write(this.props.renderer.props.list.resModel, ids, attributeValues);
            if(response){
                // Refresh the list view to reflect changes
                await this.props.renderer.props.list.model.load();
                this.notification.add("Changes applied successfully.", {
                    title: "Success",
                    type: "success",
                });
                this.goBack();
            }else{
                this.notification.add("Failed to apply changes. Please try again.", {
                    title: "Error",
                    type: "danger",
                });
            }
        }catch(err){
            this.notification.add("An error occurred while applying changes. Please try again.", {
                title: "Error",
                type: "danger",
            });
            console.error(err);
        }
    }
}
