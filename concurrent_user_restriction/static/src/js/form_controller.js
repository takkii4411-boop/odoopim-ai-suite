/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {FormController} from "@web/views/form/form_controller";
import {useService} from "@web/core/utils/hooks";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import { Component, onRendered, useEffect, useRef, useState, onWillDestroy } from "@odoo/owl";
var timerId;
var self;
patch(FormController.prototype, {
    /**
     * @override
     */
    async setup() {
        super.setup();
        onWillDestroy(() => {
            clearInterval(timerId);
        });
        self = this;
        this.state = useState({
            danger_warning:'',
            success_warning:''
        });
//        console.log("this.model.root",this.model.root)
//        console.log("this.model.root.config",this.model.root.config)
        this.update_lock_time();
        const { disableAutofocus } = this.archInfo;
        if (!disableAutofocus) {
            useEffect(
                (isInEdition) => {
                if (['product.brand','family.attribute','supplier.info','product.template','pim.attribute.type',
                'product.attribute','attribute.group','pim.category'].includes(this.model.root.resModel)){
                this._run_concurrent_fun();
                }

                    if (
                        !isInEdition &&
                        !this.rootRef.el
                            .querySelector(".o_content")
                            .contains(document.activeElement)
                    ) {
                        const elementToFocus = this.rootRef.el.querySelector(
                            ".o_content button.btn-primary"
                        );
                        if (elementToFocus) {
                            elementToFocus.focus();
                        }
                    }
                },
                () => [this.model.root.isInEdition]
            );
        }
    },
    async _run_concurrent_fun(){
        const res = await this.orm.call(this.model.root.resModel, "disable_editing", [
                    [this.model.root.resId]
                ]);
        await this.can_edit_session(this.model.root.resModel,this.model.root.resId);
    },
    async onPagerUpdate({ offset, resIds }) {

        const dirty = await this.model.root.isDirty();
        if (['product.brand','family.attribute','supplier.info','pim.category','product.template','pim.attribute.type',
                'product.attribute','attribute.group'].includes(this.model.root.resModel)){
                 await this.orm.call(this.model.root.resModel, "clear_edit_session", [
                  [this.model.root.resId]
                        ]);
                  const res = await this.orm.call(this.model.root.resModel, "disable_editing", [
                  [resIds[offset]]
                        ]);
                  await this.can_edit_session(this.model.root.resModel,resIds[offset]);
        }
        if (dirty) {
            return this.model.root.save({
                onError: this.onSaveError.bind(this),
                nextId: resIds[offset],
            });
        } else {
            return this.model.load({ resId: resIds[offset] });
        }
    },
    async onRecordSaved(record, changes) {
    console.log("before save");
//    if (this.model.root.resModel == 'product.brand'){
//     await this.orm.call(this.model.root.resModel, "enable_editing", [
//                    [this.model.root.resId]
//                ]);
//    }
        if (this.duplicateId === record.id) {
            const translationChanges = {};
            for (const fieldName in changes) {
                if (record.fields[fieldName].translate) {
                    translationChanges[fieldName] = changes[fieldName];
                }
            }
            if (Object.keys(translationChanges).length) {
                await this.orm.call(this.model.root.resModel, "web_override_translations", [
                    [this.model.root.resId]
                ]);
            }
        }
//     window.location.reload();
    },
     async beforeUnload(ev) {
      console.log("unload happens here")
      clearInterval(timerId);
        const succeeded = await this.model.root.urgentSave();
        if (!succeeded) {
            ev.preventDefault();
            ev.returnValue = "Unsaved changes";
        }
//         if (['product.brand','family.attribute','supplier.info',
//                'product.attribute','attribute.group'].includes(this.model.root.resModel)){
//         await this.orm.call(this.model.root.resModel, "clear_edit_session", [
//          [this.model.root.resId]
//                ]);
//     }
    },
    async duplicateRecord() {
     await this.dialogService.add(ConfirmationDialog, {
            title: _t("Duplicate"),
            body: _t("Are you sure that you would like to copy this record?"),
            confirm: () => {
                   super.duplicateRecord();
            },
            cancel: () => {
                // we do nothing on cancel.
            },
        });
    },
     async beforeLeave() {
     console.log("before leave");

     if (['product.brand','family.attribute','supplier.info','pim.category','product.template','pim.attribute.type',
                'product.attribute','attribute.group'].includes(this.model.root.resModel)){
                this.orm.call(this.model.root.resModel, "clear_edit_session", [
                    [this.model.root.resId]
                ]);
                }
        if (this.model.root.dirty) {
            return this.model.root.save({
                reload: true,
                onError: this.onSaveError.bind(this),
            });
        }
        console.log("timer id",timerId);
        clearInterval(timerId);
        console.log("sstimer id",timerId);
    },

    get actionMenuItems() {
        const actionMenus = super.actionMenuItems;
        if (['product.brand','family.attribute','supplier.info','pim.category','product.template','pim.attribute.type',
                'product.attribute','attribute.group'].includes(this.props.resModel)){
//        if (this.props.resModel == 'product.template') {
            const {action} = actionMenus;

            const filteredAction = action.filter((item) => item.key !== "archive" && item.key !== "unarchive" );

            actionMenus.action = filteredAction;
        }

        return actionMenus;
    },
    async can_edit_session(model,id){
        if (['product.brand','family.attribute','supplier.info','pim.category','product.template','pim.attribute.type',
                'product.attribute','attribute.group'].includes(model)){
                    const res = await this.orm.call(model, "can_edit_session", [[id]]);
                    if(res == 0){
                                    self.state.danger_warning = "You cannot edit now. Please wait.";
                                    self.state.success_warning = "";
//                                    this.props.readonly = true;
//                                    this.props.preventEdit = true;
//                                    this.canEdit = false;
                                }
                     if(res == 1){
                                    self.state.success_warning = "You can edit now";
                                    self.state.danger_warning = "";
                                }
                     if(res == 2){
                                    self.state.success_warning = "";
                                    self.state.danger_warning = "";
                                }

                }
    },
     async _myScheduledFunction(){
         if (['product.brand','family.attribute','supplier.info','pim.category','product.template','pim.attribute.type',
                'product.attribute','attribute.group'].includes(this.model.root.config.resModel)){

                    try{
                                const res = await this.orm.call(this.model.root.config.resModel, "check_lock", [
                                    [this.model.root.resId]
                                ]);
                                if (res==1){
                                console.log("relaod ")
                                    await this.orm.call(this.model.root.config.resModel, "disable_editing", [[this.model.root.config.resId]]);
                                    self.state.success_warning = "You can edit now. Please refresh";
                                    self.state.danger_warning = "";
//                                    window.location.reload();
//                                    return this.model.load({ resId: this.model.root.resId });
                                   }
                                if (res==2){
                                    console.log("this.model.root.dirty",this.model.root.dirty)
                                    self.state.danger_warning = "You cannot edit now. Please wait.";
                                    self.state.success_warning = "";
                                    await this.model.root.urgentSave();
                                    this.model.root.dirty = false;
                                    this.canEdit = false;
                                }
                            }
                        catch{
                            clearInterval(timerId);
                            console.log("catch");
                        }
                }
    },
    async reloadWindow(){
        window.location.reload();
    },

    async update_lock_time(){
              try{
                 timerId = setInterval(self._myScheduledFunction.bind(self), 8000);
                 return;
              }
              catch{
                clearInterval(timerId);
              }
    },
    async reloadForm(){
        window.location.reload();
    }
});
