/** @odoo-module **/

import { TreeFormController } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";
import { TreeFormRenderer } from "@odoopim_split_widget/views/tree_form_view/tree_form_renderer";
import { patch } from "@web/core/utils/patch";
import { LangLocalize } from "@pim_localization/localize/localize";
import { Component, useState, reactive, useRef,onWillStart, onWillUnmount, onMounted } from "@odoo/owl";
import { ProdLang } from "@pim_localization/localize/localize";


TreeFormController.components = {
    ...TreeFormController.components,
    LangLocalize
}
patch(TreeFormRenderer.prototype,{
    setup(){
        super.setup(...arguments);
        onMounted(async ()=>{
            await this._onOpenRecord();
        });
    },
    async _onOpenRecord(){
        if(ProdLang.record){
            await this.onCellClicked(ProdLang.record);
        }
    }
});