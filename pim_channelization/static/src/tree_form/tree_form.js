/** @odoo-module **/

import { TreeFormController } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";
import { TreeFormRenderer } from "@odoopim_split_widget/views/tree_form_view/tree_form_renderer";
import { patch } from "@web/core/utils/patch";
import { Component, useState, reactive, useRef,onWillStart, onWillUnmount, onMounted } from "@odoo/owl";
import { PimChannelisation } from "@pim_channelization/channelise/channelise";
import { pimGlobalChannel } from "@pim_channelization/channelise/channelise";

TreeFormController.components = {
    ...TreeFormController.components,
    PimChannelisation
}
patch(TreeFormRenderer.prototype,{
    setup(){
        super.setup(...arguments);
        onMounted(async ()=>{
            await this._onOpenRecord();
        });
    },
    async _onOpenRecord(){
        if(pimGlobalChannel.record){
            await this.onCellClicked(ProdLang.record);
        }
    }
});