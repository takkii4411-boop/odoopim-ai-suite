/** @odoo-module **/
import { FormCompiler } from "@web/views/form/form_compiler";
import { patch } from "@web/core/utils/patch";

patch(FormCompiler.prototype, {
    compileForm(el, params) {
        const res = super.compileForm(el, params);
        const classes = res.getAttribute("t-attf-class")
            const formView = res.getElementsByClassName('o_form_sheet_bg')[0]
            $(formView).addClass('customBottom')
            $($(formView).parent()).find('.o-mail-Form-chatter').addClass('customBottom')
            const newClasses = classes.replace('{{ __comp__.uiService.size < 6 ? "flex-column" : "flex-nowrap h-100" }}', 'flex-column')
            res.setAttribute("t-attf-class", `${newClasses}`);
            return res
    },
});
