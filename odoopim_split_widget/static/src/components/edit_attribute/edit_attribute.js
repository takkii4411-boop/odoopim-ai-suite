/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class EditAttribute extends Component{
    static template = "odoopim_split_widget.EditAttribute";
    static props = {
        renderer: {type: Object},
        controller: {type: Object},
        action: {type: Object},
    }

    setup() {
        super.setup();
        this.state = useState({
            attributeValues: {},
            attributes: [],
            loading: false,
        });
        if(this.props.action.attributes){
            this.state.attributes = this.props.action.attributes;
        }
        this.typeMap = {
            'simple_select': 'Dropdown',
            'multi_select': 'Multiselect',
            'color': 'Color',
            'text': 'Text',
            'textarea': 'Textarea',
            'yes_no': 'Checkbox',
            'number': 'Number',
            'price': 'Number',
            'date': 'Date',
            'datetime': 'Datetime',
        };
        this.getData();
    }

     async getData(){
        try{
            this.state.loading = true;
            let family_ids = this.props.renderer.env.model.root.selection.map(record => record.data.family_id?record.data.family_id[0]:null);
            let family = await this.props.controller.orm.searchRead("family.attribute", [['id','=',family_ids[0]]], ["id", "name", "exist_attribute_ids", "exist_group_ids"]);
            if(family && family.length > 0){
                family = family[0];
            }

            const groups = await this.props.controller.orm.searchRead("attribute.group", [['id','in',family.exist_group_ids]], ["id", "name"]);
            this.state.allGroups = {};
            if(groups && groups.length > 0){
                for(const group of groups){
                    this.state.allGroups[group.id] = group.name;
                }
            }
            this.state.loading = false;
            const allAttributes = await this.props.controller.orm.searchRead("product.attribute", [['id','in',family.exist_attribute_ids],['original_name','!=',false]], ["id", "name", "display_type", "original_name", "value_ids", "attribute_group"]);
            this.state.allAttributes = allAttributes;

            this.state.selectedAttributesObjects = [];
            this.addDynamicDataOnSelect(allAttributes);
        }catch(e){
            this.state.loading = false;
            console.error("Error in fetching data", e);
        }
     }

     tryParseNumber(value, defaultValue = NaN) {
      const result = Number(value);
      return isNaN(result) ? defaultValue : result;
    }

    onValueChange(event){
        const value = event.target.value;
        const name = event.target.name;

        if(!isNaN(this.tryParseNumber(value, NaN))){
            this.state.attributeValues[name] = this.tryParseNumber(value);
            return;
        }
        this.state.attributeValues[name] = value;
    }


    addDynamicDataOnSelect(data){
        var self = this;
        new MultiSelect(document.getElementById('attributes'), {
            data: data.map((d)=>{ return {
                    value: d.original_name,
                    otherText: d.attribute_group && d.attribute_group.length > 0 ?  self.state.allGroups[d.attribute_group[0]] || 'No Group' : 'No Group',
                    type: self.typeMap[d.display_type] || d.display_type,
                    text:d.name,
                }}),
            placeholder: 'Select Attributes',
            search: true,  // Enable the search box
            selectAll: false,  // Add a select all option
            onChange: function(value, text, element) {
                console.log('Change:', value, text, element);
            },
            onSelect: function(value, text, element) {
                self.state.attributes.push(value);
                let obj = self.state.allAttributes.find(attr => attr.original_name === value);
                if(obj){
                    self.state.selectedAttributesObjects.push(obj);
                    if(['simple_select','multi_select','color'].includes(obj.display_type)){
                          self.getAttributeValues(obj);
                    }
                }
                console.log('Selected:', value, text, element);
            },
            onUnselect: function(value, text, element) {
                self.state.attributes = self.state.attributes.filter(attr => attr != value);
                // also remove from selectedAttributesObjects
                self.state.selectedAttributesObjects = self.state.selectedAttributesObjects.filter(attr => attr.original_name != value);
                console.log('Unselected:', value, text, element);
            }
        });
    }

    async getAttributeValues(obj){
        try{
            const values = await this.props.controller.orm.searchRead("product.attribute.value", [['attribute_id','=',obj.id]], []);
            obj.all_values = values;
        } catch(e){
            console.error("Error in getAttributeValues", e);
        }
    }

    onMultiSelectChange(event){
        const value = event.target.value;
        const name = event.target.name;

        const selectedValues = parseInt(value);
        if(this.state.attributeValues[name] && this.state.attributeValues[name].length > 0){
            let isAlreadyAdded = false;
            for(const val of this.state.attributeValues[name]){
                if(val[1] === selectedValues){
                    isAlreadyAdded = true;
                    break;
                }
            }
            if(!isAlreadyAdded){
                this.state.attributeValues[name].push([4,selectedValues]);
            }else{
                // remove the value
                this.state.attributeValues[name] = this.state.attributeValues[name].filter(val => val[1] !== selectedValues);
            }
        }else{
            this.state.attributeValues[name] = [[4, selectedValues]];
        }
    }

    applyChanges(){
        for(const attrId of this.state.attributes){
            if(!Object.keys(this.state.attributeValues).includes(attrId)){
                this.props.renderer.notificationService.add("Please select value for all selected attributes.", {type: "warning"});
                return;
            }
        }
        this.props.renderer.dialogService.add(ConfirmationDialog, {
            title: "Are you sure want to confirm the changes?",
            body: `You are about to update the attribute values for ${this.props.renderer.env.model.root.selection.length} products. Please review the changes carefully to ensure that all information is accurate before you proceed. Once confirmed, these changes will be applied product details across your system.`,
            confirm: () => {
                this.props.controller.saveChanges(this.state.attributeValues);
            },
            cancel: () => {},
        });
    }

    changeStep(step){
        this.props.controller.changeStep(step);
    }

}