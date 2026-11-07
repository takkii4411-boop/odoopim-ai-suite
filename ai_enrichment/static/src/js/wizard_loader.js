/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

// We patch the FormController to intercept button clicks.
patch(FormController.prototype, {
    /**
     * @override
     */
    async _onButtonClicked(clickParams) {
        // First, check if the clicked button is our "Enrich" button.
        // The 'name' corresponds to the method name in your Python model.
        if (clickParams.name === 'action_enrich') {
            // Use the UI service to block the screen with a spinner.
            // This is the standard Odoo way to show a loader.
            this.env.services.ui.block();
            try {
                // Call the original button click handler, which will execute
                // the Python method.
                await this._super(...arguments);
            } finally {
                // Ensure the UI is unblocked, even if there's an error.
                this.env.services.ui.unblock();
            }
        } else {
            // For any other button, just call the original method without blocking.
            await this._super(...arguments);
        }
    },
});