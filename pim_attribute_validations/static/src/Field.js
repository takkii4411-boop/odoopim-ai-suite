/** @odoo-module **/
import {patch} from "@web/core/utils/patch";
import {Field} from "@web/views/fields/field";
import {onMounted, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {Record} from "@web/model/relational_model/record";
import {_t} from "@web/core/l10n/translation";

patch(Field.prototype, {
    setup() {
        super.setup();
        if (this._shouldValidate()) {
            this.orm = useService("orm");
            this.notification = useService("notification");
            this.validation = useState({error: null, isValidating: false});
            onMounted(() => this._setupValidationListener());
        }
    },

    _shouldValidate() {
        return (
            this.props.record?.resModel === "product.template" &&
            this.props.name?.startsWith("x_") &&
            !this.props.readonly
        );
    },

    _setupValidationListener() {
        const record = this.props.record;
        if (!record._pimValidationErrors) record._pimValidationErrors = {};
        if (!record._originalUpdate) {
            record._originalUpdate = record.update.bind(record);
            record.update = async (changes, options) => {
                for (const [fieldName, newValue] of Object.entries(changes)) {
                    if (fieldName.startsWith('x_')) {
                        await record._validateFieldRealtime(fieldName, newValue);
                    }
                }
                return await record._originalUpdate(changes, options);
            };
        }
        record._validateFieldRealtime = async (fieldName, value) => {
            try {
                const result = await this.orm.call(
                    "product.template",
                    "validate_dynamic_field",
                    [[record.resId || false], fieldName, value]
                );
                if (!result.valid) {
                    record._pimValidationErrors[fieldName] = {
                        field: fieldName,
                        label: result.field_label,
                        error: result.error
                    };
                    const fieldComp = (record._validationFields || new Map()).get(fieldName);
                    if (fieldComp) fieldComp._showError(result.error);
                } else {
                    delete record._pimValidationErrors[fieldName];
                    const fieldComp = (record._validationFields || new Map()).get(fieldName);
                    if (fieldComp) fieldComp._clearError();
                }
            } catch (error) {
                console.warn(`[PIM Validation] Exception during validation:`, error);
            }
        };
        if (!record._validationFields) record._validationFields = new Map();
        record._validationFields.set(this.props.name, this);
    },

    _showError(message) {
        this.validation.error = message;
    },

    _clearError() {
        this.validation.error = null;
    },

    get classNames() {
        let classes = super.classNames || "";
        if (this.validation?.error) classes += " o_pim_field_invalid";
        if (this.validation?.isValidating) classes += " o_pim_field_validating";
        return classes;
    },
});

patch(Record.prototype, {
    async _save(options = {}) {
        if (this.resModel === "product.template") {
            const errors = this._pimValidationErrors || {};
            const errorFields = Object.keys(errors);
            if (errorFields.length > 0) {
                const errorMessages = errorFields
                    .map(field => `• ${errors[field].label}: ${errors[field].error}`)
                    .join('\n');
                this.model.notification.add(
                    _t("Cannot save! Fix these errors:\n\n") + errorMessages,
                    {type: "danger", title: _t("Validation Failed"), sticky: true}
                );
                return false;
            }
        }
        return await super._save(options);
    },
});