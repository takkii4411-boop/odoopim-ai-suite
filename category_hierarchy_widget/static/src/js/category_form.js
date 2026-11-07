/** @odoo-module **/

import { registry } from "@web/core/registry";
import { createElement, append } from "@web/core/utils/xml";
import { Notebook } from "@web/core/notebook/notebook";
import { _t } from "@web/core/l10n/translation";
import { formView } from "@web/views/form/form_view";
import { FormCompiler } from "@web/views/form/form_compiler";
import { FormRenderer } from "@web/views/form/form_renderer";
import { FormController } from '@web/views/form/form_controller';
import { useService } from "@web/core/utils/hooks";
import { Component, EventBus, onWillStart, useSubEnv, useRef, useState, useChildSubEnv,} from "@odoo/owl";
import { useSortable } from "@web/core/utils/sortable_owl";
import { fuzzyLookup } from "@web/core/utils/search";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

class categoryController extends FormController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.channels = [];
        this.profiles= [];
        this.unassigned_accounts= [];
        this.profileAccounts = [];
        this.accounts= [];
        this.rootRef = useRef("root");
        this.account_list = [];
        self=this;
        this.resId = null;
        this.searchRef = useRef("search");
        this.state = useState({
            edit_allowed : [],
            categories:'',
            addMode:false,
            currentAddCateg:'',
            currentCategory:''
        });

        useSubEnv({
            overviewBus: new EventBus(),
        });
        self.getCategories();

        onWillStart(async () => {
            this.state.currentCategory = self.props.resId;
        });
        document.addEventListener('dragstart',this.ondragaccount);
        document.addEventListener("dragover", (ev) => {
          ev.preventDefault();
        });
        document.addEventListener("drop", this.ondropevent);
    }



    async openCategory(resId) {
        if (!resId || resId === this.resId) {
            return;
        }

//        try {
//        await this.model.load({ resId });
//        } catch {
//            this.dialogService.add(AlertDialog, {
//                title: _t("Access Denied"),
//                body: _t(
//                    "The article you are trying to open has either been removed or is inaccessible.",
//                ),
//                confirmLabel: _t("Close"),
//            });
//        }
//        this.state.currentCategory = resId;
//        this.toggleAsideMobile(false);
    }

    async ondragaccount(ev){
               console.log("source", ev.target.id);
               ev.dataTransfer.clearData();
               ev.dataTransfer.setData("text/plain", ev.target.id);
    }

    async ondropevent(ev){
                ev.preventDefault();
                const data = ev.dataTransfer.getData("text");
                console.log("drop event",data)
                const account = document.getElementById(data);
                const element = document.getElementById(ev.target.id);
                console.log(data,account,element,ev.target.id)
                const res = await  self.orm.call('product.category','update_parent_category', [self.props.resId,Number(data),Number(ev.target.id)]);
                self.state.categories = res;
    }
    async getCategories(){
        var jstreeData = await this.orm.call('product.category', "return_categories_hierarchy", [1]);
        Object.assign(this.state, { categories: jstreeData });
        console.log("jstreeData ",jstreeData )
    }
     async show_child_categ(target){
        const ele = target.closest('li')
        if (ele.classList.contains("jstree-closed")){
            ele.classList.remove("jstree-closed");
            ele.classList.add("jstree-open");
        }

        else if (ele.classList.contains("jstree-open")){
            ele.classList.remove("jstree-open");
            ele.classList.add("jstree-closed");
        }
    }
    async open_categ(target){
        const ele = target.closest('li')
        if (ele.classList.contains("jstree-closed")){
            ele.classList.remove("jstree-closed");
            ele.classList.add("jstree-open");
        }
        if (ele.classList.contains("jstree-leaf")){
            ele.classList.remove("jstree-leaf");
            ele.classList.add("jstree-open");
        }
    }

    SelectCategory(categ_id){
        console.log("SelectCategory",categ_id)
        cat_dialog.state.SelectedCategory = categ_id;
    }

    async addCatgeory(ev,categ_id){
               this.open_categ(ev.target);
//               this.state.addMode != true ||
               if (categ_id != this.state.currentAddCateg){
                    const parentLi = ev.target.closest("li")
                    var ul = parentLi.querySelector("ul");
                    if (!ul){
                        console.log("ullllllllllll")
                        ul = document.createElement("ul");
                        ul.classList.add("jstree-children");
                        parentLi.appendChild(ul);
                    }
                    console.log("ullll",ul);
//                    if (!this.state.currentAddCateg){
//                        if (ul) {
//                              const newLi = document.createElement("li");
//                              newLi.classList.add("my-class");
//                              const input = document.createElement("input");
//                              input.type = "text";
//                              input.classList.add("my-text-class");
//                              input.placeholder = "Enter text";
//                              newLi.id = "my-id";
//                              newLi.appendChild(input);
//                              ul.appendChild(newLi);
//                            }
//                            this.state.currentAddCateg = categ_id;
//                   }
//                   else{
                        const liToMove = document.querySelector(".my-class");
                        if (liToMove && ul) {
                          ul.appendChild(liToMove);
                        }
                        this.state.currentAddCateg = categ_id;

//                   }

                    this.state.addMode = true;
               }
      }
      async saveCategory(){
            const el = document.querySelector(".my-text-class");
            if (el){
                    const data = el.value;
                    const res = await self.orm.call('product.category','create_new_category', [self.props.resId,this.state.currentAddCateg,data]);
                    self.state.categories = res['category_tree'];
                    self.state.currentAddCateg  = false;
                    this.state.addMode = false;
//                    this.openCategory(res['new_id']);
                    el.remove();
            }
      }

    get isDebug() {
        return Boolean(odoo.debug);
    }
    async gotoHierarchicalview(){
        return self.actionService.doAction({
               name: "Categories",
               type: "ir.actions.act_window",
               res_model: "product.category",
               view_mode: "hierarchy",
               views: [[false, "hierarchy"]],
               target: "main",
            });
    }
    async gotoListView(){
        return self.actionService.doAction({
               name: "Categories",
               type: "ir.actions.act_window",
               res_model: "product.category",
               view_mode: "list",
               views: [[false, "list"]],
               target: "main",
            });
    }

    async onRecordSaved(record, changes) {

    }

    async _onclickCatgeory(ev){
         let recordId = this.props.record.resId;
         let title = 'Select a Category';
         let categList = await this.orm.call('product.category', "return_categories_hierarchy", [1]);;
         const addDialogProps = {
              title,
              recordId,
              existingCatList,
              addCategory: (category) => this.addCategory(category),
          };
          this.dialogService.add(CategoryHierarchyDialog, addDialogProps);
     }
}


//export class categoryControlPanel extends ControlPanel {
//    static template = "categoryFormControlPanel";
//}

categoryController.template = "category_template";
const categoryFormView = {
    ...formView,
//    ControlPanel: categoryControlPanel,
    Controller: categoryController,
};
registry.category("views").add("category_form_view", categoryFormView);
