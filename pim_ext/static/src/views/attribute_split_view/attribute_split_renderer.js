/** @odoo-module */
import {ListRenderer} from "@web/views/list/list_renderer";
import {FormRenderer} from "@web/views/form/form_renderer";
import {Record} from "@web/model/relational_model/record";
import {extractFieldsFromArchInfo} from "@web/model/relational_model/utils";
import {parseXML} from "@web/core/utils/xml";
import {registry} from "@web/core/registry";
import {
    markRaw,
    onWillStart,
    useState,
    onMounted,
    onWillUnmount
} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {
    ConfirmationDialog
} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {AttributeSplitBus} from "./attribute_split_controller";

const viewRegistry = registry.category("views");

export class AttributeSplitRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.formViewService = useService("view");
        this.dialog = useService("dialog");
        this.actionService = useService("action");
        this.lastSplitWidths = {left: 58.33, right: 41.67};
        this.isDragging = false;
        this.isAnimating = false;
        this.isDragActive = false;
        this.attributeState = useState({
            selectedAction: false,
            current_record: null,
            isCreating: false,
            isSelectingType: false,
        });
        this.realModelName = "Attribute"; // Default
        this.cleanupFunctions = [];
        AttributeSplitBus.addEventListener("open-split", (ev) => {
            const {record, isCreating, isSelectingType} = ev.detail;
            this.attributeState.current_record = record;
            this.attributeState.isCreating = isCreating;
            this.attributeState.isSelectingType = isSelectingType;
        });
        AttributeSplitBus.addEventListener("close-split", () => {
            this.closeSplitView();
        });
        onMounted(() => {
            this.ensureListFullWidth();
            this.fixFormLayout();
            this._extractModelName();
        });
        onWillUnmount(() => {
            this.cleanupFunctions.forEach(fn => fn());
            this.cleanupFunctions = [];
        });
        onWillStart(async () => {
            try {
                await this.loadFormView();
            } catch (error) {
                this.dialog.add(ConfirmationDialog, {
                    title: _t("Error"),
                    body: _t("Failed to load form view. Please refresh."),
                });
            }
        });
    }

    async _extractModelName() {
        try {
            const realModelName = await this.orm.searchRead("ir.model", [["model", "=", this.props.list.resModel]], ["name"]);
            if (realModelName.length > 0) {
                this.realModelName = realModelName[0].name;
            }
        } catch (error) {
            console.error("Failed to extract model name:", error);
        }
    }

    // Open record in full-screen form view
    async onPencilClickFullScreen(record, ev) {
        ev.stopPropagation();
        ev.preventDefault();
        try {
            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: this.props.list.resModel,
                res_id: record.resId,
                views: [[false, 'form']],
                target: 'current',
                context: this.props.list.context,
            });
        } catch (error) {
            console.error("Failed to open form view:", error);
            this.env.services.notification.add(
                "Failed to open form view",
                {type: "danger"}
            );
        }
    }

    ensureListFullWidth() {
        const listPanel = document.querySelector('.attribute-split-list');
        if (!this.attributeState.current_record && listPanel) {
            listPanel.style.width = "100%";
            listPanel.style.flex = "1";
        }
    }

    fixFormLayout() {
        const style = document.createElement('style');
        style.id = 'attribute-split-form-fix';
        style.textContent = `
            .o_pim_attribute_split_view .attribute-split-form .o_form_view {
                display: flex !important;
                flex-direction: column;
                min-width: 0 !important;
                max-width: 100% !important;
            }
            .o_pim_attribute_split_view .attribute-split-form .o_form_sheet_bg {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            .o_pim_attribute_split_view .attribute-split-form .o_form_sheet {
                flex: 1;
                max-width: 100% !important;
                box-shadow: none !important;
                border: none !important;
                background: transparent !important;
            }
        `;
        if (!document.getElementById('attribute-split-form-fix')) {
            document.head.appendChild(style);
        }
    }

    async loadFormView() {
        const resModel = this.props.list.resModel;
        const formID = this.getFormViewId() || false;
        const result = await this.formViewService.loadViews({
            context: this.props.list.context,
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
        const view = viewRegistry.get("form");
        const {archInfo} = view.props(viewProps, view);
        const {activeFields} = extractFieldsFromArchInfo(archInfo, fields);
        Object.assign(this.attributeState, {archInfo, fields, activeFields});
    }

    getFormViewId() {
        for (const [viewId, viewType] of this.env.config.views || []) {
            if (viewType === "form") return viewId;
        }
        return false;
    }

    async onCellClicked(record, column, ev) {
        ev.stopPropagation();
        ev.preventDefault();
        if (this.isDragging || this.isAnimating) return;
        // Auto-save if there are changes
        if (this.attributeState.current_record && this.props.controllerRef?.isFormChanged) {
            try {
                await this.props.controllerRef.onClickSave();
            } catch (e) {
                console.warn("Auto-save failed:", e);
                return;
            }
        }
        // If clicking the same record, just reload it
        if (this.attributeState.current_record?.resId === record.resId) {
            await this.reloadCurrentRecord(record);
            return;
        }
        this.isAnimating = true;
        if (this.attributeState.current_record) {
            await this.animateRecordSwitch();
        }
        await this.openRecordInSplitView(record);
    }

    async openRecordInSplitView(record) {
        try {
            const records = await this.props.list.model._loadRecords({
                resModel: this.props.list.resModel,
                resIds: [record.resId],
                activeFields: this.attributeState.activeFields,
                fields: this.attributeState.fields,
                context: this.props.list.context,
            });
            const model = this.props.list.model;
            model.hooks.onRecordChanged = this.onRecordChanged.bind(this);
            this.attributeState.current_record = new Record(model, {
                ...this.props.list.model.config,
                mode: "edit",
                isMonoRecord: true,
                resId: record.resId,
                resIds: [record.resId],
                resModel: this.props.list.resModel,
                activeFields: this.attributeState.activeFields,
                fields: this.attributeState.fields,
                context: this.props.list.context,
            }, records[0]);
            if (this.props.controllerRef?.openRecord) {
                await this.props.controllerRef.openRecord(
                    this.attributeState.current_record,
                    this.lastSplitWidths.left || 58.33,
                    this.lastSplitWidths.right || 41.67,
                    false,
                    false
                );
            }
        } catch (error) {
            console.error("Error opening record:", error);
        } finally {
            setTimeout(() => {
                this.fixFormLayout();
                this.isAnimating = false;
            }, 300);
        }
    }

    async reloadCurrentRecord(record) {
        if (!this.attributeState.current_record) return;
        this.isAnimating = true;
        try {
            await this.attributeState.current_record.load();
            await this.props.list.model.load();
        } finally {
            setTimeout(() => this.isAnimating = false, 200);
        }
    }

    async animateRecordSwitch() {
        const formPanel = document.querySelector('.attribute-split-form');
        if (!formPanel) return;
        formPanel.classList.add('record-switching');
        await new Promise(r => setTimeout(r, 300));
        formPanel.classList.remove('record-switching');
    }

    onRecordChanged(record, changes) {
        if (this.props.controllerRef) {
            this.props.controllerRef.onFormChange(record, changes);
        }
    }

    getRowClass(record) {
        let cls = super.getRowClass(record);
        if (this.attributeState.current_record?.resId === record.resId) {
            cls += " o_data_row_active";
        }
        return cls;
    }

    onStartSplitResize(ev) {
        if (!ev.target.classList.contains('attribute-split-resize')) return;
        ev.preventDefault();
        ev.stopPropagation();
        // TOGGLE DRAG MODE
        if (this.isDragActive) {
            this.isDragActive = false;
            document.body.classList.remove('dragging-resize');
            this.isDragging = false;
            const leftPanel = document.querySelector('.attribute-split-list');
            const rightPanel = document.querySelector('.attribute-split-form');
            if (leftPanel) leftPanel.classList.remove('no-transition');
            if (rightPanel) rightPanel.classList.remove('no-transition');
            return;
        }
        // Start drag mode
        this.isDragActive = true;
        this.isDragging = true;
        const parent = document.querySelector('.o_content');
        const leftPanel = document.querySelector('.attribute-split-list');
        const rightPanel = document.querySelector('.attribute-split-form');
        if (!leftPanel || !rightPanel || !parent) return;
        leftPanel.classList.add('no-transition');
        rightPanel.classList.add('no-transition');
        document.body.classList.add('dragging-resize');
        const parentRect = parent.getBoundingClientRect();
        const padding = 48;
        const handleMargins = 32;
        const availableWidth = parentRect.width - padding - handleMargins;
        // Mouse move handler
        const onMouseMove = (e) => {
            if (!this.isDragging) return;
            const mouseX = e.clientX - parentRect.left - 24;
            const leftPx = Math.max(300, Math.min(mouseX, availableWidth - 300));
            const leftPercent = (leftPx / availableWidth) * 100;
            const rightPercent = 100 - leftPercent;
            leftPanel.style.width = `${leftPx}px`;
            rightPanel.style.width = `${availableWidth - leftPx}px`;
            this.lastSplitWidths = {left: leftPercent, right: rightPercent};
        };
        // Mouse up handler
        const onMouseUp = () => {
            this.isDragging = false;
            // Keep drag mode active until clicked again
            // this.isDragActive remains true
            leftPanel.classList.remove('no-transition');
            rightPanel.classList.remove('no-transition');
            document.body.classList.remove('dragging-resize');
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    closeSplitView() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        const leftPanel = document.querySelector(".attribute-split-list");
        const rightPanel = document.querySelector(".attribute-split-form");
        if (rightPanel) {
            rightPanel.classList.add('closing-animation');
            setTimeout(() => {
                if (leftPanel) {
                    leftPanel.style.width = "100%";
                }
                if (rightPanel) rightPanel.style.width = "0";
                setTimeout(() => {
                    this.attributeState.current_record = null;
                    this.attributeState.isCreating = false;
                    this.attributeState.isSelectingType = false;
                    if (this.props.controllerRef) {
                        this.props.controllerRef.splitState.currentRecord = null;
                        this.props.controllerRef.splitState.isCreating = false;
                        this.props.controllerRef.splitState.isSelectingType = false;
                        this.props.controllerRef.currentRecord = null;
                        this.props.controllerRef.isFormChanged = false;
                        this.props.controllerRef.render();
                    }
                    rightPanel.classList.remove('closing-animation');
                    this.isAnimating = false;
                }, 400);
            }, 50);
        } else {
            this.attributeState.current_record = null;
            this.attributeState.isCreating = false;
            this.attributeState.isSelectingType = false;
            if (this.props.controllerRef) {
                this.props.controllerRef.splitState.currentRecord = null;
                this.props.controllerRef.splitState.isCreating = false;
                this.props.controllerRef.splitState.isSelectingType = false;
                this.props.controllerRef.currentRecord = null;
                this.props.controllerRef.isFormChanged = false;
                this.props.controllerRef.render();
            }
            if (leftPanel) leftPanel.style.width = "100%";
            this.isAnimating = false;
        }
    }
}

AttributeSplitRenderer.template = "pim_ext.AttributeSplitRenderer";
AttributeSplitRenderer.components = {...ListRenderer.components, FormRenderer};
AttributeSplitRenderer.props = [...ListRenderer.props, "onFormChange?", "onClickSave?", "controllerRef?", "realModelName?"];