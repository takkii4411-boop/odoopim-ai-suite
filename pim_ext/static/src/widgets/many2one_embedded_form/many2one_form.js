/** @odoo-module **/

import { formView } from "@web/views/form/form_view";
import { patch } from "@web/core/utils/patch";
import { markRaw, onWillStart, useState, useEffect, useComponent } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { FormRenderer } from "@web/views/form/form_renderer";
import { parseXML } from "@web/core/utils/xml";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field";
import { extractFieldsFromArchInfo } from "@web/model/relational_model/utils";
import { Record } from "@web/model/relational_model/record";
import { Model } from "@web/model/model";
import {debounce} from "@web/core/utils/timing";
import {ListController} from "@web/views/list/list_controller";


const viewRegistry = registry.category("views");

//patch(ListController.prototype,{
//    async onClickSave() {
//        console.log("hello mc", this)
//        return super.onClickSave(...arguments);
//    }
//});

class Many2OneFieldForm extends Many2OneField {
    static template = "pim_ext.Many2OneFieldForm";
    static components = { FormRenderer, Many2XAutocomplete };
    async setup() {
        super.setup();
        this.orm = useService("orm");
        this.viewService = useService("view");
        this.actionService = useService("action");
        // State to store embedded form
        this.embeddedForm = useState({
            arch: null,
            fields: {},
            resId: false,
            model: null,
            recordData: null,
        });
        console.log(this)
        var recordData = await this.load_embedded_form(this.resId)
    }
    updateRecord(value) {
        var res = super.updateRecord(...arguments);
        this.load_embedded_form(value[0])
        return res;
    }
    async load_embedded_form(value){

        const resModel = this.relation
        const {fields, relatedModels, views: {form: {arch}}} = await this.viewService.loadViews({
                context: this.context || {},
                resModel: resModel,
                views: [[false, 'form']],
            });
        const archXmlDoc = parseXML(arch);
        const viewProps = {
            arch: archXmlDoc,
            fields: fields,
            relatedModels: markRaw(relatedModels),
            resModel,
        }
        const fieldNames = Object.keys(fields);
        const [recordData] = await this.orm.read(this.relation, [value], fieldNames);
        const new_record = new Record(this.env.model, {
            ...this.env.model.config,
            mode: 'edit',
            isMonoRecord: true,
            resId: value,
            resIds: [value],
            resModel: resModel,
            activeFields: fields,
            fields: fields,
            context: this.context,
        }, recordData);
        this.embeddedForm.recordData = new_record;
        const view = viewRegistry.get('form');
        const { archInfo } = view.props(viewProps, view);
        const { activeFields } = extractFieldsFromArchInfo(
            archInfo,
            fields
        );
        Object.assign(this.embeddedForm, {
            archInfo,
            fields,
            activeFields
        });
        return new_record;
    }
    async onClickDiscardForm(){
        this.embeddedForm.recordData.discard();
        console.log(this)
    }
    async onClickSaveForm(){
//        debugger;
//        this.embeddedForm.recordData._save()
        await this.orm.write(
            this.embeddedForm.recordData.resModel,
            [this.embeddedForm.recordData.resId],
            this.embeddedForm.recordData._changes
        );
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "display_notification",
            params: {
                title: this.displayName || 'Success',
                message: "Changes Saved Successfully",
                type: "success",
                sticky: false,
            },
        });
    }
}

export const many2OneFieldForm = {
    ...many2OneField,
    component: Many2OneFieldForm,
};

registry.category("fields").add("many2one_form", many2OneFieldForm);
