/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { useService } from "@web/core/utils/hooks";


patch(ControlPanel.prototype, {
    get model_name(){
        const url = window.location.href
        const match = url.match(/model=([^&]+)/);
        var model = 'default'
        if (match){
            model = match[1]
        }
        console.log('----------------------model',model)
        return model
    }

    });





