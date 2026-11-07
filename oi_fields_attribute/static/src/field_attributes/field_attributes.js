/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { toPyValue, formatAST} from "@web/core/py_js/py_utils";

export class FieldAttributesDialog extends Component {
    static template = "oi_fields_attribute.FieldAttributes";
    static components = { Dialog };
    static defaultProps = {
        title: _t("Field Attributes"),
    };

    get data () {
        return this.props.info;
    }

    isFunction(value) {
        return (Array.isArray(value) && value.length===3 && value[0] === "$FUNC");
    }

    formatValue(value) {
        const ast = toPyValue(value);
        return formatAST(ast);
    }

}

export async function fieldAttributesAction(env, action) {    
    const {params} = action;
    const info = await env.services.rpc(`/oi_fields_attribute/${params.type || 'info'}`, {
        field_id: action.context.active_id
    });
    const dialogProps = {
        info
    };    
    env.services.dialog.add(FieldAttributesDialog, dialogProps);
}


registry.category("actions").add("field_attributes", fieldAttributesAction);