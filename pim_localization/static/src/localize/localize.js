/* @odoo-module */

import { Component, useState, reactive, useRef,onWillStart, onWillUnmount, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { loadLanguages, _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { viewService } from "@web/views/view_service";

import { TreeFormControllerBus } from "@odoopim_split_widget/views/tree_form_view/tree_form_controller"

export const ProdLang = reactive({
    product_lang: { id:1, code:'en_US', label:"English (US)" },
    record: false
});
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export class LangLocalize extends Component{
    static template = "pim_localization.LangLocalize";
    static props = {
        model: { type: Object },
    };
    async setup(){
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.input = useRef("search");
        this.LanguagesDrop = useRef("LanguagesDrop");
        this.state = useState({
            lang: 1,
            languages : [],
            filterLang : [],
            show_drop: false
        });

        onWillStart(async () => {
            // 1. Load languages: expecting [(id, code, label)]
            const langs = await this.orm.searchRead("res.lang",[['active','=',true]],['id','code', 'name'])
            console.log(langs)
            this.state.languages = langs;
            this.state.filterLang = langs;
            // 2. Load user data: m_lang_id = [id, code, name]
            const [userData] = await this.orm.searchRead(
                "res.users",
                [["id", "=", user.userId]],
                ["m_lang_id"]
            );
            let productLangId = false;
            if (userData.m_lang_id) {
                productLangId = userData.m_lang_id[0];   // ← ID
            }
            // 3. Set selected lang as ID only
            const productLangObj = langs.find(l => l.id === productLangId);
            this.state.lang = productLangId || 1;
        });

        onMounted(async () => {
            this.handleClickOutside = this.handleClickOutside.bind(this);
            this.setGlobal();
        });

        onWillUnmount(() => {
            document.removeEventListener("click", this.handleClickOutside);
            this.setGlobal();
        });
    }
    ClickOpenLanguages(){
        if(this.state.show_drop == true){
            this.state.show_drop = false;
            document.removeEventListener('click', this.handleClickOutside);
            return;
        }
        this.state.show_drop = true;
        setTimeout(() => {
            document.addEventListener('click', this.handleClickOutside);
        }, 0);
        return;
    }
    async SelectLang(lang){
        console.log(lang)
        await this.orm.write('res.users', [user.userId], { m_lang_id: lang.id  });
        this.state.show_drop = false;
        this.setGlobal();
        this.state.lang = lang.id
        const viewService = this.env.services.view;
        if (viewService?.clearCache) {
            viewService.clearCache();
        } else {
            this.env.bus.trigger("CLEAR-CACHES");
        }
        var [id] = await this.orm.searchRead("ir.ui.view",[['xml_id','=','pim_ext.view_product_product_management_tree']],['id']);
        var record = this.props.model.editedRecord;
        ProdLang.record = record;
        await this.action.doAction({
            type: 'ir.actions.client',
            tag: 'soft_reload',
        });
    }
    handleClickOutside(ev) {
        const dropdown = this.LanguagesDrop.el;
        if (dropdown && !dropdown.contains(ev.target)) {
            this.state.show_drop = false;
            document.removeEventListener('click', this.handleClickOutside);
        }
    }
    onSearchInput() {
        const query = this.input.el.value.toLowerCase();
        this.state.filterLang = this.state.languages.filter(lang =>
            lang.label.toLowerCase().includes(query)
        );
    }
    setGlobal(){
        ProdLang.id = this.state.lang;
    }
    get currentLang() {
        return this.state.languages.find(l => l.id === this.state.lang);
    }
}