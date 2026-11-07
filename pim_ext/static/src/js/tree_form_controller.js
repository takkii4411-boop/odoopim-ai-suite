/** @odoo-module **/

import { reactive } from "@odoo/owl";

import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { TreeFormController } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";
import { useEffect,useState } from "@odoo/owl";
import { user } from "@web/core/user";
import { loadLanguages, _t } from "@web/core/l10n/translation";

patch(TreeFormController.prototype, {
    setup() {
        this.orm = useService("orm");
        super.setup();
    },
    async onClickSave() {
        if( this.myState.editedRecord.resModel != this.model.root.resModel){
            await this.orm.write(
                this.myState.editedRecord.resModel,
                [this.myState.editedRecord.resId],
                this.myState.editedRecord._changes
            );
            await this.model.root.leaveEditMode();
            return;
        }
        return super.onClickSave(...arguments);
    },
});
