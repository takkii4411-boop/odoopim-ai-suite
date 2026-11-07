/** @odoo-module **/
import {patch} from "@web/core/utils/patch";
import {Field} from "@web/views/fields/field";
import {onWillStart, onWillUpdateProps} from "@odoo/owl";
import {useState} from "@odoo/owl";

patch(Field.prototype, {
    setup() {
        super.setup();

        // Add stateful variable
        this.fieldState = useState({
            showNA: false
        });

        onWillStart(async () => {
            this.checkIfFieldIsNA();
        });

        onWillUpdateProps(async (nextProps) => {
            this.checkIfFieldIsNA(nextProps);
        });
    },

    checkIfFieldIsNA(nextProps = null) {
        const props = nextProps || this.props;
        const record = props.record;
        const fieldName = props.name;

        // Reset state
        this.fieldState.showNA = false;

        // Step 1: Check if res_model is product.template
        if (!['product.template', 'product.product'].includes(record.resModel)) {
            return;
        }

        // Step 2: ONLY process fields that start with x_
        if (!fieldName.startsWith('x_')) {
            return;
        }

        // Step 3: Get is_na JSON data from record
        const isNaData = record.data.is_na;

        // If no is_na data, skip
        if (!isNaData || typeof isNaData !== 'object') {
            return;
        }

        // Step 4: Check if current field exists in is_na.fields
        const fieldsData = isNaData.fields || {};
        const fieldInfo = fieldsData[fieldName];

        // Step 5: If field has is_na = true, show NA
        if (fieldInfo && fieldInfo.is_na === true) {
            this.fieldState.showNA = true;
        }
    },
});
