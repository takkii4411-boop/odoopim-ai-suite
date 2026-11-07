/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TreeFormController } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller";


patch(TreeFormController.prototype, {
    async setup() {
        super.setup(...arguments);

        this.myState.isCreateProductOpen = false;
        this.myState.showSyncLogs = false;
        localStorage.setItem("ai_enrichment_done", "false");
    },

    toggleCreateProduct() {
        this.myState.isCreateProductOpen = !this.myState.isCreateProductOpen;
        if (this.myState.isCreateProductOpen) {
            this.setLeftRightWidth(60, 40);
        } else {
            this.setLeftRightWidth(100, 0);
        }
    },

    closeActions() {
        super.closeActions();
        if (this.myState.isCreateProductOpen) {
            this.toggleCreateProduct();
        }
    },

    openSyncLogs() {
        const orm = this.env.services.orm;

        orm.searchRead(
            "ai.enrichment.queue.log",
            [],
            ["id"],
            { limit: 1, order: "id desc" }
        ).then((logs) => {
            if (!logs.length) {
                this.env.services.notification.add("No Sync Logs found.", {
                    type: "warning",
                });
                return;
            }

            const latestId = logs[0].id;

            this.env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: "ai.enrichment.queue.log",
                res_id: latestId,
                views: [[false, "form"]],
                target: "current",
            });
        });
    },
});
