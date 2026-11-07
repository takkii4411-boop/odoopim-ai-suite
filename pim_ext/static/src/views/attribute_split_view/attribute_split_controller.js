/** @odoo-module */
import {ListController} from "@web/views/list/list_controller";
import {executeButtonCallback} from "@web/views/view_button/view_button_hook";
import {
    useState,
    EventBus,
    onWillStart,
    markRaw,
    onMounted,
    onWillUnmount
} from "@odoo/owl";
import {Record} from "@web/model/relational_model/record";
import {extractFieldsFromArchInfo} from "@web/model/relational_model/utils";
import {parseXML} from "@web/core/utils/xml";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export const AttributeSplitBus = new EventBus();

export class AttributeSplitController extends ListController {
    setup() {
        super.setup();
        this.splitState = useState({
            isFilterOpened: false,
            isCreating: false,
            isSelectingType: false,
            currentRecord: null,
        });
        this.isFormChanged = false;
        this.currentRecord = null;
        this.formArchInfo = null;
        this.formFields = null;
        this.formActiveFields = null;
        this.viewService = useService("view");
        this.companyService = useService("company");
        this.orm = useService("orm");
        this.realModelName = "Attribute"; // Default
        onWillStart(async () => {
            await this._extractModelName();
            await this.loadFormFields();
        });
        onMounted(() => {
            this.setupControlPanelButtons();
        });
        onWillUnmount(() => {
            this.cleanupControlPanelButtons();
        });
        this.props.Renderer.defaultProps = {
            ...this.props.Renderer.defaultProps,
            controllerRef: this,
            realModelName: this.realModelName,
        };
        AttributeSplitBus.addEventListener("CLOSE_ACTIONS", this.closeActions.bind(this));
    }

    async _extractModelName() {
        try {
            const realModelName = await this.orm.searchRead("ir.model", [["model", "=", this.props.resModel]], ["name"]);
            if (realModelName.length > 0) {
                this.realModelName = realModelName[0].name;
            }
        } catch (error) {
            console.error("Failed to extract model name:", error);
        }
    }

    setupControlPanelButtons() {
        setTimeout(() => {
            const controlPanelNav = document.querySelector('.o_control_panel_navigation');
            if (!controlPanelNav) return;
            if (document.querySelector('[data-pim-buttons="true"]')) return;
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'o_cp_action_menus d-flex align-items-center gap-2';
            buttonContainer.setAttribute('data-pim-buttons', 'true');
            this.updateButtonContainer(buttonContainer);
            const pager = controlPanelNav.querySelector('.o_cp_pager');
            if (pager) {
                controlPanelNav.insertBefore(buttonContainer, pager);
            } else {
                controlPanelNav.insertBefore(buttonContainer, controlPanelNav.firstChild);
            }
        }, 100);
    }

    updateButtonContainer(container) {
        container.innerHTML = '';
        if (this.isFormChanged) {
            const saveBtn = this.createButton('save', 'Save', 'fa-check', 'btn-success o_list_button_save', 's');
            const discardBtn = this.createButton('discard', 'Discard', 'fa-times', 'btn-secondary o_list_button_discard', 'j');
            const btnGroup = document.createElement('div');
            btnGroup.className = 'd-flex gap-2';
            btnGroup.appendChild(saveBtn);
            btnGroup.appendChild(discardBtn);
            container.appendChild(btnGroup);
        }
        // Only show Create button for product.attribute
        if (this.props.resModel === 'product.attribute') {
            const createBtn = this.createButton('create', 'Create Attribute', 'fa-plus', 'btn-primary o_list_button_create', 'c');
            container.appendChild(createBtn);
        }
    }

    createButton(action, text, icon, btnClass, hotkey) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `btn ${btnClass} d-flex align-items-center`;
        btn.setAttribute('data-hotkey', hotkey);
        btn.title = text;
        const iconEl = document.createElement('i');
        iconEl.className = `fa ${icon} me-1`;
        btn.appendChild(iconEl);
        const spanEl = document.createElement('span');
        spanEl.className = 'd-none d-lg-inline';
        spanEl.textContent = text;
        btn.appendChild(spanEl);
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            if (action === 'save') this.onClickSave();
            else if (action === 'discard') this.onClickDiscard();
            else if (action === 'create') this.onCreateAttribute();
        });
        return btn;
    }

    cleanupControlPanelButtons() {
        const buttons = document.querySelector('[data-pim-buttons="true"]');
        if (buttons) buttons.remove();
    }

    async loadFormFields() {
        if (this.formArchInfo) return;
        try {
            const resModel = this.props.resModel;
            const formID = this.getFormViewId() || false;
            const result = await this.viewService.loadViews({
                context: this.props.context,
                resModel,
                views: [[formID, "form"]],
            }, {actionId: this.env.config.actionId});
            const {fields, relatedModels, views} = result;
            const arch = views.form.arch;
            const archXmlDoc = parseXML(arch);
            const viewProps = {
                arch: archXmlDoc,
                fields,
                relatedModels: markRaw(relatedModels),
                resModel
            };
            const view = registry.category("views").get("form");
            const {archInfo} = view.props(viewProps, view);
            const extractedFields = extractFieldsFromArchInfo(archInfo, fields);
            this.formActiveFields = extractedFields.activeFields;
            this.formFields = fields;
            this.formArchInfo = archInfo;
        } catch (error) {
            console.error("Failed to load form fields:", error);
            this.env.services.notification.add("Failed to load form configuration", {type: "danger"});
        }
    }

    getFormViewId() {
        for (const [viewId, viewType] of this.env.config.views || []) {
            if (viewType === "form") return viewId;
        }
        return false;
    }

    openRecord(record, leftPercent = 58.33, rightPercent = 41.67, isCreating = false, isSelectingType = false) {
        this.closeActions();
        const parent = document.querySelector(".o_content");
        const leftPanel = document.querySelector(".attribute-split-list");
        const rightPanel = document.querySelector(".attribute-split-form");
        if (parent && leftPanel) {
            const parentWidth = parent.getBoundingClientRect().width;
            const padding = 48;
            const handleMargins = 32;
            const availableWidth = parentWidth - padding - handleMargins;
            const leftWidth = (availableWidth * leftPercent) / 100;
            const rightWidth = (availableWidth * rightPercent) / 100;
            leftPanel.style.width = `${leftWidth}px`;
            if (rightPanel) {
                rightPanel.style.width = `${rightWidth}px`;
                if (!rightPanel.classList.contains('first-open-animation')) {
                    rightPanel.classList.add("slide-in-right");
                    setTimeout(() => rightPanel.classList.remove("slide-in-right"), 400);
                }
            }
        }
        this.currentRecord = record;
        this.splitState.currentRecord = record;
        this.splitState.isCreating = isCreating;
        this.splitState.isSelectingType = isSelectingType;
        AttributeSplitBus.trigger("open-split", {
            record,
            isCreating,
            isSelectingType
        });
        this.render();
    }

    closeActions() {
        if (this.splitState.isFilterOpened) this.toggleFilter();
    }

    onFormChange(record, changes) {
        this.isFormChanged = true;
        this.splitState.currentRecord = record;
        const buttonContainer = document.querySelector('[data-pim-buttons="true"]');
        if (buttonContainer) {
            this.updateButtonContainer(buttonContainer);
        }
        this.render();
    }

    async onCreateAttribute() {
        this.closeActions();
        await this.loadFormFields();
        this.openRecord(null, 58.33, 41.67, true, true);
    }

    async onTypeSelected(displayType) {
        await this.loadFormFields();
        if (!this.formArchInfo || !this.formActiveFields) {
            console.error("Form fields still not available after loading");
            this.env.services.notification.add("Form configuration is not ready. Please try again.", {type: "danger"});
            return;
        }
        try {
            let currentCompanyId = null;
            if (this.companyService && this.companyService.currentCompany) {
                currentCompanyId = this.companyService.currentCompany.id;
            } else if (this.props.context.allowed_company_ids && this.props.context.allowed_company_ids.length > 0) {
                currentCompanyId = this.props.context.allowed_company_ids[0];
            }
            const fieldNames = Object.keys(this.formActiveFields);
            const contextWithDefaults = {
                ...this.props.context,
                default_display_type: displayType,
            };
            if (currentCompanyId) {
                contextWithDefaults.default_company_id = currentCompanyId;
            }
            const defaults = await this.env.services.orm.call(
                this.props.resModel,
                "default_get",
                [fieldNames],
                {context: contextWithDefaults}
            );
            defaults.display_type = displayType;
            if (!defaults.company_id && currentCompanyId) {
                defaults.company_id = currentCompanyId;
            }
            const initialData = {};
            for (const fieldName in this.formFields) {
                const field = this.formFields[fieldName];
                if (defaults.hasOwnProperty(fieldName) && defaults[fieldName] !== false) {
                    if (field.type === 'many2one') {
                        if (Array.isArray(defaults[fieldName])) {
                            initialData[fieldName] = defaults[fieldName][0];
                        } else {
                            initialData[fieldName] = defaults[fieldName];
                        }
                    } else {
                        initialData[fieldName] = defaults[fieldName];
                    }
                } else if (field.type === 'many2one') {
                    if (fieldName === 'company_id' && currentCompanyId) {
                        initialData[fieldName] = currentCompanyId;
                    } else {
                        initialData[fieldName] = false;
                    }
                } else if (field.type === 'one2many' || field.type === 'many2many') {
                    initialData[fieldName] = [];
                } else if (field.type === 'boolean') {
                    initialData[fieldName] = false;
                } else {
                    initialData[fieldName] = false;
                }
            }
            const recordData = {
                id: false,
                ...initialData
            };
            const model = this.model;
            const newRecord = new Record(model, {
                resModel: this.props.resModel,
                resId: false,
                resIds: [],
                activeFields: this.formActiveFields,
                fields: this.formFields,
                context: contextWithDefaults,
                mode: "edit",
                isMonoRecord: true,
            }, recordData);
            this.splitState.isSelectingType = false;
            this.splitState.isCreating = true;
            this.isFormChanged = true;
            const buttonContainer = document.querySelector('[data-pim-buttons="true"]');
            if (buttonContainer) {
                this.updateButtonContainer(buttonContainer);
            }
            this.openRecord(newRecord, 58.33, 41.67, true, false);
        } catch (error) {
            console.error("Failed to create attribute form:", error);
            this.env.services.notification.add(`Failed to open form: ${error.message || 'Unknown error'}`, {type: "danger"});
        }
    }

    async onClickSave() {
        if (!this.isFormChanged) return;
        const record = this.currentRecord || this.splitState.currentRecord;
        if (!record) {
            console.error("No record to save");
            return;
        }
        return executeButtonCallback(this.rootRef.el, async () => {
            try {
                const saved = await record.save();
                if (saved) {
                    const newRecordId = record.resId;
                    await this.model.load();
                    const records = await this.model._loadRecords({
                        resModel: this.props.resModel,
                        resIds: [newRecordId],
                        activeFields: this.formActiveFields,
                        fields: this.formFields,
                        context: this.props.context,
                    });
                    const savedRecord = new Record(this.model, {
                        resModel: this.props.resModel,
                        resId: newRecordId,
                        resIds: [newRecordId],
                        activeFields: this.formActiveFields,
                        fields: this.formFields,
                        context: this.props.context,
                        mode: "edit",
                        isMonoRecord: true,
                    }, records[0]);
                    this.currentRecord = savedRecord;
                    this.splitState.currentRecord = savedRecord;
                    this.isFormChanged = false;
                    this.splitState.isCreating = false;
                    const buttonContainer = document.querySelector('[data-pim-buttons="true"]');
                    if (buttonContainer) {
                        this.updateButtonContainer(buttonContainer);
                    }
                    this.render();
                    this.env.services.notification.add("Attribute saved successfully", {type: "success"});
                }
            } catch (error) {
                console.error("Save failed:", error);
                let errorMessage = error.message || 'Unknown error';
                if (error.data && error.data.message) {
                    errorMessage = error.data.message;
                }
                this.env.services.notification.add(`Save failed: ${errorMessage}`, {type: "danger"});
            }
        });
    }

    async onClickDiscard() {
        return executeButtonCallback(this.rootRef.el, async () => {
            if (this.splitState.isSelectingType) {
                AttributeSplitBus.trigger("close-split");
                return;
            }
            const record = this.currentRecord || this.splitState.currentRecord;
            if (this.splitState.isCreating && (!record || !record.resId)) {
                AttributeSplitBus.trigger("close-split");
            } else if (record && record.resId) {
                await record.discard();
                await record.load();
                await this.model.load();
            } else {
                AttributeSplitBus.trigger("close-split");
            }
            this.isFormChanged = false;
            const buttonContainer = document.querySelector('[data-pim-buttons="true"]');
            if (buttonContainer) {
                this.updateButtonContainer(buttonContainer);
            }
            this.render();
        });
    }

    toggleFilter() {
        this.splitState.isFilterOpened = !this.splitState.isFilterOpened;
        const leftPanel = document.querySelector(".attribute-split-list");
        const rightPanel = document.querySelector(".attribute-split-form");
        if (this.splitState.isFilterOpened) {
            leftPanel.style.width = "75%";
            rightPanel && (rightPanel.style.width = "25%");
        } else {
            leftPanel.style.width = "100%";
            rightPanel && (rightPanel.style.width = "0%");
        }
    }
}

AttributeSplitController.template = "pim_ext.AttributeSplitView";