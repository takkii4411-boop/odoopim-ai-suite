/** @odoo-module **/
import {CharField} from "@web/views/fields/char/char_field";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";


patch(CharField.prototype, {
    setup() {
        super.setup();
    },

    /**
     * Override the parse method to capitalize the first letter
     * @param {String} value - The input value
     * @returns {String} - The processed value with first letter capitalized
     */
    parse(value) {
        // Call the original parse method first (handles trimming if needed)
        let parsedValue = super.parse(value);

        // Check if capitalization is enabled
        if (!session.enable_char_capitalize) {
            return parsedValue;
        }

        // Get the current model and field name
        const currentModel = this.props.record.resModel;
        const currentField = this.props.name;
        const fullFieldName = `${currentModel}.${currentField}`;

        // Get excluded lists
        const excludedModels = session.excluded_models_capitalize || [];
        const excludedFields = session.excluded_fields_capitalize || [];

        // Check if current model is in the excluded models list
        const isModelSelected = excludedModels.includes(currentModel);

        // Get all excluded fields for the current model
        const modelSpecificFields = excludedFields.filter(field =>
            field.startsWith(currentModel + '.')
        );

        // Determine if capitalization should be skipped
        let shouldSkipCapitalization = false;

        if (isModelSelected) {
            // Model is selected
            if (modelSpecificFields.length > 0) {
                // Case 1: Model selected + has specific fields
                // Only skip if this specific field is excluded
                shouldSkipCapitalization = excludedFields.includes(fullFieldName);
            } else {
                // Case 2: Model selected + NO specific fields
                // Skip all char fields in this model
                shouldSkipCapitalization = true;
            }
        }

        // Capitalize the first letter if value exists and should not be skipped
        if (parsedValue && parsedValue.length > 0 && !shouldSkipCapitalization) {
            parsedValue = parsedValue.charAt(0).toUpperCase() + parsedValue.slice(1);
        }

        return parsedValue;
    },
});
