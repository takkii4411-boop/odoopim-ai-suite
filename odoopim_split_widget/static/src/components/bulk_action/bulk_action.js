/** @odoo-module */

import { Component, useState } from "@odoo/owl";

/*
-----All the actions available-----
EDIT_ATTRIBUTES_VALUES
ADD_ATTRIBUTES_VALUES
CHANGE_FAMILY
CHANGE_STATUS
ADD_TO_GROUPS
ADD_TO_CATEGORIES
MOVE_BETWEEN_CATEGORIES
REMOVE_FROM_CATEGORIES
ADD_TO_AN_EXISTING_PRODUCT_MODEL
CHANGE_THE_PARENT_PRODUCT_MODEL
CONVERT_TO_SIMPLE_PRODUCTS
ASSOCIATE

*/

export class BulkAction extends Component{
    static template = "odoopim_split_widget.BulkAction";
    static props = {
        isFormChange: {type: Boolean, optional: true},
        renderer: {type: Object},
        controller: {type: Object},
        actions: {type: Array, optional: false},
    }

    setup() {
        super.setup();
        this.state = useState({
            selectedAction: false,
        });
        this.isFormChange = false;
    }

    changeAction(action){
        this.state.selectedAction = action;
        this.props.controller.changeBulkAction(action);
    }

   async changeStep(step){

        if(this.state.selectedAction === 'PUBLISH_TO_CHANNEL'){


//            let ids = this.props.renderer.env.model.root.selection.map(record => record.data.id);
            let ids = this.props.renderer.props.list.selection.map(rec => rec.data.id);
            var action = "odoo_pim_connector.action_push_to_channel"
            if (this.props.renderer.resModel == 'product.product'){
                action = "odoo_pim_connector.action_push_to_channel_variant"
            }
            await this.props.renderer.actionService.doAction(action, {
                additionalContext: {
                    active_ids: ids,
                    active_model: this.props.renderer.resModel
                }
            });
            this.props.controller.goBack();
            return;
        }else if(this.state.selectedAction === 'EDIT_ATTRIBUTES_VALUES' || this.state.selectedAction === 'ADD_ATTRIBUTES_VALUES'){
            let family_ids = this.props.renderer.env.model.root.selection.map(record => record.data.family_id?record.data.family_id[0]:null);
            if(!family_ids[0]){
                this.props.controller.notification.add("Selected products do not belong to any family. Cannot edit or add attribute values.", {
                    title: "No Family Assigned",
                    type: "danger",
                });
                return;
            }
            // ensure all selected products belong to the same family
            const allSameFamily = family_ids.every(val => val === family_ids[0]);
            if(!allSameFamily){
                this.props.controller.notification.add("Selected products must belong to the same family to edit or add attribute values.", {
                    title: "Inconsistent Families",
                    type: "danger",
                });
                return;
            }

        }
        this.props.controller.changeStep(step);
    }
}
