/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { useSelectCreate, useOpenMany2XRecord} from "@web/views/fields/relational_utils";
import { Record } from "@web/model/relational_model/record";
import { Field } from "@web/views/fields/field";
import { useRecordObserver, getFieldsSpec, FetchRecordError } from "@web/model/relational_model/utils";
import { StaticList } from "@web/model/relational_model/static_list";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { Component, useRef, useState, onWillStart, onRendered, markRaw } from "@odoo/owl";
import { Domain } from "@web/core/domain";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";

patch(StaticList.prototype, {
    load({ limit, offset, orderBy, domain } = {}) {
        return this.model.mutex.exec(async () => {
            if (this.editedRecord && !(await this.editedRecord.checkValidity())) {
                return;
            }
            limit = limit !== undefined ? limit : this.limit;
            offset = offset !== undefined ? offset : this.offset;
            orderBy = orderBy !== undefined ? orderBy : this.orderBy;
            domain = domain !== undefined ? domain : [];
            return this._load({ limit, offset, orderBy, domain });
        });
    },
    async _load({ limit, offset, orderBy, nextCurrentIds, domain } = {}) {
        limit = limit !== undefined ? limit : this.limit;
        offset = offset !== undefined ? offset : this.offset;
        orderBy = orderBy !== undefined ? orderBy : this.orderBy;
        domain = domain !== undefined ? domain : [];
        nextCurrentIds = nextCurrentIds !== undefined ? nextCurrentIds : this._currentIds;
        const currentIds = nextCurrentIds.slice(offset, offset + limit);
        const resIds = this._getResIdsToLoad(currentIds);
        if (resIds.length) {
            const records = await this.model._loadRecords(
                { ...this.config, resIds },
                this.evalContext
            );
            for (const record of records) {
                this._createRecordDatapoint(record);
            }
        }
        this.records = currentIds.map((id) => this._cache[id]);
        this._currentIds = nextCurrentIds;
        await this.model._updateConfig(this.config, { limit, offset, orderBy }, { reload: false });
    }
})

patch(RelationalModel.prototype,{

    async _loadRecords(config, evalContext = config.context) {
        const { resModel, resIds, activeFields, fields, context, x2many_plus_domain} = config;
        if (!resIds.length) {
            return [];
        }
        const fieldSpec = getFieldsSpec(activeFields, fields, evalContext);
        if(!x2many_plus_domain){
            if (Object.keys(fieldSpec).length > 0) {
                const kwargs = {
                    context: { bin_size: true, ...context },
                    specification: fieldSpec,
                };
                const records = await this.orm.webRead(resModel, resIds, kwargs);
                if (!records.length) {
                    throw new FetchRecordError(resIds);
                }

                return records;
            } else {
                return resIds.map((resId) => {
                    return { id: resId };
                });
            }
        } else {
            const kwargs = {
                context: { bin_size: true, ...context, x2many_plus_domain },
                specification: fieldSpec
            };
            const records = await this.orm.webRead(resModel, resIds, kwargs);
            return records;
        }

    },
    async _updateConfig(config, patch, { reload = true, commit } = {}) {
        const tmpConfig = { ...config, ...patch };
        markRaw(tmpConfig.activeFields);
        markRaw(tmpConfig.fields);

        let data;
        if (reload) {
            data = await this._loadData(tmpConfig);
        }
        Object.assign(config, tmpConfig);
        if (data && commit) {
            commit(data);
        }
    },

    async _updateCount(config) {
        const count = await this.keepLast.add(this.orm.searchCount(config.resModel, config.domain));
        config.countLimit = Number.MAX_SAFE_INTEGER;
        return count;
    }
})

export class X2ManyPlusField extends X2ManyField {
    static template = "web.X2ManyPlusField";
    setup() {
        super.setup();
        this.action = useService("action");
        this.Domain = Domain;
        this.orm = useService("orm");
        this.search_panel = useRef('search_panel');
        this.filter_fields = [];
        this.filter_fields_name = [];
        let fieldNodes = Object.values(this.rendererProps.archInfo.fieldNodes);

        for(let i=0; i<fieldNodes.length; i++){
            if(fieldNodes[i].options.filter){
                this.filter_fields.push(fieldNodes[i]);
                this.filter_fields_name.push(fieldNodes[i].name);
            }
        }
        let activeFields = {}
        for(let i in this.list._config.activeFields){
//            console.log(this.list._config.activeFields[i])
            activeFields[i] = {
                'context': '{}',
                'forceSave': true,
                'readonly': 'False',
                'onChange': false,
                'required': 'False'
            }
        }
        this.default_record = new Record(this.list.model, {
            ...this.list._config,
            mode: 'edit',
            resId: undefined,
            resIds: [],
            activeFields: Object.assign({}, activeFields),
        }, {})
    }

    get_search_domain(){
        let search_domain=[];
        for(let i in this.filter_fields_name){
            let _value = this.default_record.evalContext[this.filter_fields_name[i]];
            let attrs = this.filter_fields.filter(r => r.name == this.filter_fields_name[i])[0].attrs;
            if(_value && attrs['filter_domain']){
                search_domain = this.Domain.and([search_domain,attrs['filter_domain'].replace(/self/g, "'"+_value+"'")]).toList();
            }
            if(_value && !attrs['filter_domain']){
                search_domain.push([this.filter_fields_name[i], '=', _value]);
            }
        }
        return search_domain;
    }

    async subTreeReload(e){
        let search_domain=this.get_search_domain();

        if(search_domain.length==0){
            this.list.load();
            return;
        }
        let list_parent = this.rendererProps.list
        let resIds = list_parent.config.resIds
        search_domain.push(['id', 'in', resIds])
        let x2many_plus_domain = search_domain
        let currentIds = []
        let records = await list_parent.model._loadRecords(
            { ...list_parent.config, resIds, x2many_plus_domain },
            list_parent.evalContext
        );
        for (const record of records) {
            list_parent._createRecordDatapoint(record);
            currentIds.push(record.id)
        }
        list_parent.records = currentIds.map((id) => list_parent._cache[id]);
        this.render();
    }

    async printOnline(e){
        let search_domain=this.get_search_domain();
        let list_parent = this.rendererProps.list
        let resIds = list_parent.config.resIds
        search_domain.push(['id', 'in', resIds])
        let x2many_plus_domain = search_domain
        let _config = this.rendererProps.list._parent._config;
        const _action = await this.orm.call(
            _config.resModel, "action_print_report", [_config.resId], {
                context: { ..._config.context, ...{x2many_plus_domain} },
            }
        );
        this.action.doAction(_action);
    }

    async exportOnline(e){
        let search_domain=this.get_search_domain();
        let list_parent = this.rendererProps.list
        let resIds = list_parent.config.resIds
        search_domain.push(['id', 'in', resIds])
        let x2many_plus_domain = search_domain
        let o_list_renderer = $(e.target.parentElement).siblings('.o_list_renderer');
        let column_ids = [];
        let columns = [];
        let _config = this.rendererProps.list._config;
        o_list_renderer.find('thead>tr>th:not([class*=o_list_record_selector])').each(function () {
            if($(this).attr('data-name')){
                column_ids.push($(this).attr('data-name'));
                columns.push(this.textContent);
            }
        });
        const __fieldsSpec = getFieldsSpec(_config.activeFields, _config.fields, _config.context);
        let fields_info = {};
        for (let i = 0; i < column_ids.length; i++) {
            fields_info[column_ids[i]] = __fieldsSpec[column_ids[i]];
        }
        await download({
            data: {
                data: JSON.stringify({
                    model: this.props.crudOptions.exportFileName,
                    resModel: _config.resModel,
                    domain: search_domain,
                    headers: columns,
                    fields: column_ids,
                    fields_info: fields_info,
                    context: _config.context
                }),
            },
            url: `/web/export/xls_view_all`,
        });
    }

}

X2ManyPlusField.components = {
    ...X2ManyField.components,
    Field,
}

export const x2ManyPlusField = {
    ...x2ManyField,
    component: X2ManyPlusField,
};

registry.category("fields").add("x2many_plus", x2ManyPlusField);
