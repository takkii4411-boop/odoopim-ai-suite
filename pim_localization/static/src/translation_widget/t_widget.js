/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { TranslationDialog } from "@web/views/fields/translation_dialog";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { loadLanguages, _t } from "@web/core/l10n/translation";
import { jsToPyLocale } from "@web/core/l10n/utils";

export class FieldTranslateWidget extends Component {
    static template = "pim_localization.FieldTranslateWidget";
    static components = { TranslationDialog };
    static props = {
        id: { type: [String, Number], optional: true },
        name: { type: String },
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        value: { type: [String, Boolean, Number, Object], optional: true },

        userLanguageValue: { type: String, optional: true },
        isComingFromTranslationAlert: { type: Boolean, optional: true },
         onSave: { type: Function, optional: true },
        isText: { type: Boolean, optional: true },
        showSource: { type: Boolean, optional: true },
    };
    async setup(){
        super.setup();
        this.title = _t("Translate: %s", this.props.name);
        this.user = user;
        this.orm = useService("orm");
        this.state = useState({
            terms:[],
            updatedTerms: {}
        })
        onWillStart(async () => {
            await this.update_terms_vals();
        });
    }
    async update_terms_vals(){
        const languages = await loadLanguages(this.orm);
        const [translations, context] = await this.loadTranslations(languages);
        let id = 1;
        translations.forEach((t) => (t.id = id++));
        this.props.isText = context.translation_type === "text";
        this.props.showSource = context.translation_show_source;
        this.state.terms = translations.map((term) => {
            const relatedLanguage = languages.find((l) => l[0] === term.lang);
            const termInfo = {
                ...term,
                langName: relatedLanguage[1],
                value: term.value || "",
            };
            // we set the translation value coming from the database, except for the language
            // the user is currently utilizing. Then we set the translation value coming
            // from the value of the field in the form
            if (
                term.lang === jsToPyLocale(user.lang) &&
                !this.props.showSource &&
                !this.props.isComingFromTranslationAlert
            ) {
                this.state.updatedTerms[term.id] = this.props.record.data[this.props.name];
                termInfo.value = this.props.record.data[this.props.name];
            }
            return termInfo;
        });
        this.state.terms.sort((a, b) => a.langName.localeCompare(b.langName));
    }
    async loadTranslations(languages) {
        return this.orm.call(this.props.record.resModel, "get_field_translations", [
            [this.props.record.resId],
            this.props.name,
        ]);
    }
    async onSave() {
        const translations = {};

        this.state.terms.map((term) => {
            const updatedTermValue = this.state.updatedTerms[term.id];
            if (term.id in this.state.updatedTerms && term.value !== updatedTermValue) {
                if (this.props.showSource) {
                    if (!translations[term.lang]) {
                        translations[term.lang] = {};
                    }
                    translations[term.lang][term.source] = updatedTermValue || term.source;
                } else {
                    translations[term.lang] = updatedTermValue || false;
                }
            }
        });
        await this.orm.call(this.props.record.resModel, "update_field_translations", [
            [this.props.record.resId],
            this.props.name,
            translations,
        ]);
        this.update_ir_field_translations(translations)
        this.props.record.save();
        await this.props.record.load();
        await this.update_terms_vals();
    }
    async update_ir_field_translations(translations){
//        if(this.props.record.resModel == "product.attribute"){
            await this.orm.call("ir.model.fields", "update_field_translations", [
                [this.props.record.data.product_template_field_id[0]],
                'field_description',
                translations,
            ]);
            await this.orm.call("ir.model.fields", "update_field_translations", [
                [this.props.record.data.product_product_field_id[0]],
                'field_description',
                translations,
            ]);
//        }
    }
}

export const fieldTranslateWidget = {
    component: FieldTranslateWidget,
};

registry.category("fields").add("t_widget", fieldTranslateWidget);
