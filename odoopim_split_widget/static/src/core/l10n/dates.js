/** @odoo-module **/

import {Record} from "@web/model/relational_model/record";
import {patch} from "@web/core/utils/patch";
import {serializeDate} from "@web/core/l10n/dates";
import { toRaw, markRaw } from "@odoo/owl";

import {
    FetchRecordError,
    createPropertyActiveField,
    getBasicEvalContext,
    getFieldContext,
    getFieldsSpec,
    parseServerValue,
} from "@web/model/relational_model/utils";

const {DateTime} = luxon;

const dateTimeCache = new WeakMap();

const SERVER_DATE_FORMAT = "yyyy-MM-dd";
const SERVER_TIME_FORMAT = "HH:mm:ss";
const SERVER_DATETIME_FORMAT = `${SERVER_DATE_FORMAT} ${SERVER_TIME_FORMAT}`;

const _fromSQL = DateTime.fromSQL;

DateTime.fromSQL = (text, opts = {}) => {
    return _fromSQL(text, {numberingSystem: "latn", zone: "default"});
}

function serializeDateTimeExtend(value) {
    if (!dateTimeCache.has(value)) {
        dateTimeCache.set(
            value,
            value.setZone("default").toFormat(SERVER_DATETIME_FORMAT, {numberingSystem: "latn"})
        );
    }
    return dateTimeCache.get(value);
}

patch(Record.prototype, {
    _computeDataContext() {
        const dataContext = {};
        const x2manyDataContext = {
            withVirtualIds: {},
            withoutVirtualIds: {},
        };
        const data = toRaw(this.data);
        for (const fieldName in data) {
            const value = data[fieldName];
            const field = this.fields[fieldName];
            if (field.relatedPropertyField) {
                continue;
            }
            if (["char", "text", "html"].includes(field.type)) {
                dataContext[fieldName] = this._textValues[fieldName];
            } else if (field.type === "one2many" || field.type === "many2many") {
                x2manyDataContext.withVirtualIds[fieldName] = value.currentIds;
                x2manyDataContext.withoutVirtualIds[fieldName] = value.currentIds.filter(
                    (id) => typeof id === "number"
                );
            } else if (value && field.type === "date") {
                dataContext[fieldName] = serializeDate(value);
            } else if (value && field.type === "datetime") {
                dataContext[fieldName] = serializeDateTimeExtend(value);
            } else if (value && field.type === "many2one") {
                dataContext[fieldName] = value[0];
            } else if (value && field.type === "reference") {
                dataContext[fieldName] = `${value.resModel},${value.resId}`;
            } else if (field.type === "properties") {
                dataContext[fieldName] = value.filter(
                    (property) => !property.definition_deleted !== false
                );
            } else {
                dataContext[fieldName] = value;
            }
        }
        dataContext.id = this.resId || false;
        return {
            withVirtualIds: {...dataContext, ...x2manyDataContext.withVirtualIds},
            withoutVirtualIds: {...dataContext, ...x2manyDataContext.withoutVirtualIds},
        };
    },

    _formatServerValue(fieldType, value) {
        if (fieldType === "date") {
            return value ? serializeDate(value) : false;
        } else if (fieldType === "datetime") {
            return value ? serializeDateTimeExtend(value) : false;
        } else if (fieldType === "char" || fieldType === "text") {
            return value !== "" ? value : false;
        } else if (fieldType === "html") {
            return value && value.length ? value : false;
        } else if (fieldType === "many2one") {
            return value ? value[0] : false;
        } else if (fieldType === "reference") {
            return value && value.resModel && value.resId
                ? `${value.resModel},${value.resId}`
                : false;
        } else if (fieldType === "properties") {
            return value.map((property) => {
                let value;
                if (property.type === "many2one") {
                    value = property.value;
                } else if (
                    (property.type === "date" || property.type === "datetime") &&
                    typeof property.value === "string"
                ) {
                    // TO REMOVE: need refactoring PropertyField to use the same format as the server
                    value = property.value;
                } else {
                    value = this._formatServerValue(property.type, property.value);
                }
                return {
                    ...property,
                    value,
                };
            });
        }
        return value;
    },

    async _save({ reload = true, onError, nextId } = {}) {
        if (this.model._closeUrgentSaveNotification) {
            this.model._closeUrgentSaveNotification();
        }
        const creation = !this.resId;
        if (nextId) {
            if (creation) {
                throw new Error("Cannot set nextId on a new record");
            }
            reload = true;
        }
        // before saving, abandon new invalid, untouched records in x2manys
        for (const fieldName in this.activeFields) {
            const field = this.fields[fieldName];
            if (["one2many", "many2many"].includes(field.type) && !field.relatedPropertyField) {
                this.data[fieldName]._abandonRecords();
            }
        }
        if (!this._checkValidity({ displayNotification: true })) {
            return false;
        }
        const changes = this._getChanges();
        delete changes.id; // id never changes, and should not be written
        if (!creation && !Object.keys(changes).length) {
            return true;
        }
        if (this.model._urgentSave && this.model.useSendBeaconToSaveUrgently) {
            // We are trying to save urgently because the user is closing the page. To
            // ensure that the save succeeds, we can't do a classic rpc, as these requests
            // can be cancelled (payload too heavy, network too slow, computer too fast...).
            // We instead use sendBeacon, which isn't cancellable. However, it has limited
            // payload (typically < 64k). So we try to save with sendBeacon, and if it
            // doesn't work, we will prevent the page from unloading.
            const route = `/web/dataset/call_kw/${this.resModel}/web_save`;
            const params = {
                model: this.resModel,
                method: "web_save",
                args: [this.resId ? [this.resId] : [], changes],
                kwargs: { context: this.context, specification: {} },
            };
            const data = { jsonrpc: "2.0", method: "call", params };
            const blob = new Blob([JSON.stringify(data)], { type: "application/json" });
            const succeeded = navigator.sendBeacon(route, blob);
            if (!succeeded) {
                this.model._closeUrgentSaveNotification = this.model.notification.add(
                    markup(
                        _t(
                            `Heads up! Your recent changes are too large to save automatically. Please click the <i class="fa fa-cloud-upload fa-fw"></i> button now to ensure your work is saved before you exit this tab.`
                        )
                    ),
                    { sticky: true }
                );
            }
            return succeeded;
        }
        const canProceed = await this.model.hooks.onWillSaveRecord(this, changes);
        if (canProceed === false) {
            return false;
        }
        let fieldSpec = {};
        if (reload) {
            fieldSpec = getFieldsSpec(
                this.activeFields,
                this.fields,
                getBasicEvalContext(this.config)
            );
        }
        const kwargs = {
            context: this.context,
            specification: fieldSpec,
            next_id: nextId,
        };
        let records = [];
        try {
            records = await this.model.orm.webSave(
                this.resModel,
                this.resId ? [this.resId] : [],
                changes,
                kwargs
            );
        } catch (e) {
            if (onError) {
                return onError(e, { discard: () => this._discard() });
            }
            if (!this.isInEdition) {
                await this._load({});
            }
            throw e;
        }
        if (reload && !records.length) {
            if(records.type && records.type=='ir.actions.act_window' && records.res_model=='new.plan.reason.wizard'){
                await this.model.action.doAction(records, { onClose: () => this._load() });
                return true;
            }else{
                throw new FetchRecordError(nextId || this.resId);
            }
        }
        if (creation) {
            const resId = records[0].id;
            const resIds = this.resIds.concat([resId]);
            this.model._updateConfig(this.config, { resId, resIds }, { reload: false });
        }
        await this.model.hooks.onRecordSaved(this, changes);
        if (reload) {
            if (this.resId) {
                this.model._updateSimilarRecords(this, records[0]);
            }
            if (nextId) {
                this.model._updateConfig(this.config, { resId: nextId }, { reload: false });
            }
            if (this.config.isRoot) {
                this.model.hooks.onWillLoadRoot(this.config);
            }
            this._setData(records[0]);
        } else {
            this._values = markRaw({ ...this._values, ...this._changes });
            if ("id" in this.activeFields) {
                this._values.id = records[0].id;
            }
            for (const fieldName in this.activeFields) {
                const field = this.fields[fieldName];
                if (["one2many", "many2many"].includes(field.type) && !field.relatedPropertyField) {
                    this._changes[fieldName]?._clearCommands();
                }
            }
            this._changes = markRaw({});
            this.data = { ...this._values };
            this.dirty = false;
        }
        return true;
    }
})