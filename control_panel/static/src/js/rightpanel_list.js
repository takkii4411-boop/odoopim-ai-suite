/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { _lt } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
const { Component, onWillStart, useState ,onMounted} = owl;
const componentModel = "product.template";
import { registry } from "@web/core/registry";
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { ListRenderer } from "@web/views/list/list_renderer";
import { unique } from "@web/core/utils/arrays";
import { Domain } from "@web/core/domain";
import { rpc } from "@web/core/network/rpc";

var custom_discontinued = false;

export class RightPanel extends Component {
    static template = "control_panel.RightPanel";
    static props = {
//        context: { type: Object },
        currentSelection: { type: Array },
        selection: { type: Array },
        model: { type: Object },
        archInfo: { type: Object },
        optionalActiveFields : { type: Object },
        fields: { type: Object },
//        edit_allowed:{type:String}
//        kanbanModel: { type: Object },
//        canCreate: { type: Boolean },
    };


    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.orm = useService("orm");
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
//        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.state = useState({
            skuCount: 0,
            familyCount: 0,
            edit_allowed:true,
        });
        onWillStart(async () => {
//            await this._loadMassActions(this.props);
//            await this._loadExportConf(this.props);
        });

    }

     async getExportedFields(model, import_compat, parentParams) {
        const fields = await this.rpc("/web/export/get_fields", { ...parentParams, model, import_compat });
        return fields
    }

    async downloadExport(fields, import_compat, format) {
        let ids = false;
        let recordIds = []
     this.props.currentSelection.forEach(function (record) {
            recordIds.push(record.resId);
        });

        const exportedFields = fields.map((field) => ({
            name: field.name || field.id,
            label: field.label || field.string,
            store: field.store,
            type: field.field_type || field.type,
        }));
        if (import_compat) {
            exportedFields.unshift({
                name: "id",
                label: _t("External ID"),
            });
        }
        await download({
            data: {
                data: JSON.stringify({
                    import_compat,
                    context: this.props.context,
                    domain: this.props.model.root.domain,
                    fields: exportedFields,
                    groupby: this.props.model.root.groupBy,
                    ids:recordIds.length > 0 && recordIds,
                    model: this.props.model.root.resModel,
                }),
            },
            url: `/web/export/${format}`,
        });
    }
    get defaultExportList() {
        return unique(
            this.props.archInfo.columns
                .filter((col) => col.type === "field")
                .filter((col) => !col.optional || this.props.optionalActiveFields[col.name])
                .map((col) => this.props.fields[col.name])
                .filter((field) => field.exportable !== false)
        );
    }
    async getExportedFields(model, import_compat, parentParams) {
        return await this.rpc("/web/export/get_fields", {
            ...parentParams,
            model,
            import_compat,
        });
    }
    async onClickExport(props){
        const dialogProps = {
                context: this.props.context,
                defaultExportList: [],
                download: this.downloadExport.bind(this),
                getExportedFields: this.getExportedFields.bind(this),
                root: this.props.model.root,
            };
            this.dialogService.add(ExportDataDialog, dialogProps);
    }

    async onClickImport(){
     const { context, resModel } = this.env.searchModel;
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "import",
            params: { model: 'family.attribute', context:this.props.context },
        });
    }
    async can_edit(){
        if (this.props.currentSelection.length){
            const edit_allowed = await this.orm.call('family.attribute','check_access', [this.props.currentSelection[0].resId]);
            console.log("this.props.currentSelection[0].resId",this.props.currentSelection[0].resId)
            this.state.edit_allowed = edit_allowed;
        }
    }


    async onClickComplementaryCategory(){
//         await this.can_edit();
         console.log(this.state.edit_allowed);
         if (!this.state.edit_allowed){
            this.notification.add("You dont have permission to add Complementary category !!!", {
                    title: "Warning",
                    type: "danger",
                });
         }
         else{

             let idlist = []
             let categ_list = []
             this.props.currentSelection.forEach(function (record) {
                    idlist.push(record.resId);
                });

               const result = await this.orm.search("family.category",[]);
               for (const categ of result)
               {
                    let categ_line = {
                        'category_id':categ
                    }
                    categ_list.push((0, 0, categ_line))
                }
                console.log("this.state.edit_allowed",this.state.edit_allowed)
                return this.actionService.doAction({
                    name: "Add Category",
                    type: "ir.actions.act_window",
                    res_model: "category.wizard",
                    views: [[false, "form"]],
                    view_mode: "form",
                    target: "new",
                    context:{'default_family_ids':idlist,
                             'default_category_ids':categ_list,
                             'default_mode':'add_comp'
                     }
                });
         }
    }

     async onClickSubstitutefamily(){
//     await this.can_edit();
         console.log(this.state.edit_allowed);
         if (!this.state.edit_allowed){
            this.notification.add("You dont have permission to add Substitute Families !!!", {
                    title: "Warning",
                    type: "danger",
                });
         }
         else{
             let idlist = []
             let family_list = []
             this.props.currentSelection.forEach(function (record) {
                    idlist.push(record.resId);
                });

//               const result = await this.orm.search("family.attribute",[]);
//               for (const  family of result)
//               {
//                    let family_line = {
//                        'family_id': family
//                    }
//                    family_list.push((0, 0, family_line))
//               }
                return this.actionService.doAction({
                    name: "Add Substitute Family",
                    type: "ir.actions.act_window",
                    res_model: "sub.family.wizard",
                    views: [[false, "form"]],
                    view_mode: "form",
                    target: "new",
                    context:{'default_family_ids':idlist,
//                             'default_sub_family_ids':family_list
                     }
                });
                }
     }

     async onClickAddCatgeory(props){
         console.log(this.state.edit_allowed);
         if (!this.state.edit_allowed){
             this.notification.add("You dont have permission to add Category !!!", {
                    title: "Warning",
                    type: "danger",
             });
         }
         else{
             let idlist = []
             let categ_list = []
             this.props.currentSelection.forEach(function (record) {
                    idlist.push(record.resId);
             });

             const result = await this.orm.search("pim.category",[]);
             for (const categ of result)
                 {
                     let categ_line = {
                        'pim_category_id':categ
                     }
                    categ_list.push((0, 0, categ_line))
                 }
                return this.actionService.doAction({
                    name: "Add Category",
                    type: "ir.actions.act_window",
                    res_model: "category.wizard",
                    views: [[false, "form"]],
                    view_mode: "form",
                    target: "new",
                    context:{'default_product_ids':idlist,
//                             'default_category_ids':categ_list,
                     }
                });
            }

     }
     async onClickCloneSKU(){
//            await this.can_edit();
         console.log(this.state.edit_allowed);
         if (!this.state.edit_allowed){
            this.notification.add("You dont have permission to add Clone SKU !!!", {
                    title: "Warning",
                    type: "danger",
                });
         }
         else{
             let idlist = []
             this.props.currentSelection.forEach(function (record) {
                    idlist.push(record.resId);
                });

                let sku_list = [];
                const view_id = await this.orm.call('family.attribute','get_sku_grid_view', [idlist[0]]);
                const res_id = await this.orm.call('family.attribute','create_sku_wizard', [idlist[0],'clone']);
                   return this.actionService.doAction({
                    name: "Choose SKU",
                    type: "ir.actions.act_window",
                    res_model: "sku.grid.wizard",
                    views: [[view_id, "form"]],
                    view_mode: "form",
                    res_id: res_id,
                    target: "new",
                });
                }
     }

     async onClickMoveSKU(){
//        await this.can_edit();
         console.log(this.state.edit_allowed);
         if (!this.state.edit_allowed){
            this.notification.add("You dont have permission to move SKU!!!", {
                    title: "Warning",
                    type: "danger",
                });
         }
         else{
             let idlist = []
             this.props.currentSelection.forEach(function (record) {
                    idlist.push(record.resId);
                });

                let sku_list = [];
                const view_id = await this.orm.call('family.attribute','get_sku_grid_view', [idlist[0]]);
                const res_id = await this.orm.call('family.attribute','create_sku_wizard', [idlist[0],'move']);
                   return this.actionService.doAction({
                    name: "Choose SKU",
                    type: "ir.actions.act_window",
                    res_model: "sku.grid.wizard",
                    views: [[view_id, "form"]],
                    view_mode: "form",
                    res_id: res_id,
                    target: "new",
                });
                }
     }

     async onClickMoveSKUnewfamily(){
//            await this.can_edit();
         console.log(this.state.edit_allowed);
         if (!this.state.edit_allowed){
            this.notification.add("You dont have permission to move SKU!!!", {
                    title: "Warning",
                    type: "danger",
                });
         }
         else{
                 let idlist = []
             this.props.currentSelection.forEach(function (record) {
                    idlist.push(record.resId);
                });

                let sku_list = [];
                const view_id = await this.orm.call('family.attribute','get_sku_grid_view', [idlist[0]]);
                const res_id = await this.orm.call('family.attribute','create_sku_wizard', [idlist[0],'move_new']);
                   return this.actionService.doAction({
                    name: "Choose SKU",
                    type: "ir.actions.act_window",
                    res_model: "sku.grid.wizard",
                    views: [[view_id, "form"]],
                    view_mode: "form",
                    res_id: res_id,
                    target: "new",
                });
                }
     }

     async onclickAddRelatedFamily(){
         console.log(this.state.edit_allowed);
         let idlist = []
         let family_list = []
         this.props.currentSelection.forEach(function (record) {
                idlist.push(record.resId);
            });
            return this.actionService.doAction({
                name: "Add Family",
                type: "ir.actions.act_window",
                res_model: "family.wizard",
                views: [[false, "form"]],
                view_mode: "form",
                target: "new",
                context:{'default_product_ids':idlist,
                 }
            });

     }

    async get_family_count(){
       const result = await this.orm.search("family.attribute", []);
       this.state.familyCount = result.length;
    }

    get family_count(){
        this.get_family_count();
        return this.state.familyCount;
    }

    async get_sku_length(res_id){
        if (this.props.currentSelection){
              const result = await this.orm.search("family.products", [['family_id','=',this.props.currentSelection[0].resId]]);
              this.state.skuCount = result.length;
        }
    }

    get sku_len() {
        this.get_sku_length();
        return this.state.skuCount;
    }

    get records() {
        return this.props.currentSelection.length;
    }
};

export class ProductListController extends ListController {
        setup() {
               super.setup();
               this.actionService = useService("action");
               this.show_discontinued = custom_discontinued;
               this.disc_element = false;

            onMounted(() => {
                    console.log("custom_discontinued",custom_discontinued);
                    if (custom_discontinued){
                        this.showarchived();
                    }
//                    else{
//                        this.hidearchived();
//                    }

                })

           }
           showarchived() {
                custom_discontinued = true;
                this.show_discontinued = true;
                var domain = [['active', 'in', [true,false]]];
                this.env.searchModel.discontinued_domain = domain;
                this.env.searchModel.PushDiscontinuedDomain();
           }
           hidearchived() {
                custom_discontinued = false;
                this.show_discontinued = false;
                var domain = [];
                this.env.searchModel.discontinued_domain = domain;
                 this.env.searchModel.PushDiscontinuedDomain();
           }
};
ProductListController.template = "control_panel.productListView";
//ProductListController.props = {
//    ...ListController.props,
//    show_archived: { type: Boolean },
//}
//ProductListController.defaultProps = {
//    ...ListController.defaultProps,
//    show_archived: () => getDefaultTitle(),
//};

export class ProductListRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }
    getFamilyManagerProps() {
        console.log("this.optionalActiveFields",this.optionalActiveFields,this.fields)
        return {
            currentSelection: this.props.list.selection || [],
            selection: this.props.list.model.selectedRecords || [],
            model: this.props.list.model,
            archInfo : this.props.archInfo,
            optionalActiveFields : this.optionalActiveFields,
            fields: this.fields,
        };
    }
}
ProductListRenderer.props = [
    ...listView.Renderer.props,
    "showButtons",
];
ProductListRenderer.template = "control_panel.ProductRenderer";
ProductListRenderer.components = Object.assign({}, ListRenderer.components, {
    RightPanel,
});


export const productListView = {
    ...listView,
    Controller: ProductListController,
    Renderer: ProductListRenderer,
//    searchMenuTypes: ["filter", "favorite"],
};

registry.category("views").add("list_panel",productListView);
