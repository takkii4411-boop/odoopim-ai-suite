/** @odoo-module **/
import { Component , useState,onWillStart,onWillUpdateProps} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { CategoryHierarchyDialog } from "@category_hierarchy_widget/js/category_dialog";
import { rpc } from "@web/core/network/rpc";

export class enhancedCategorywidget extends Component {
    static template = 'CategoryHierarchyTemplate'
    setup(){
       super.setup();
       this.dialogService = useService("dialog");
       this.orm = useService("orm");
         this.state = useState({
            isValid:'',
            categories:'',
            addMode:false,
            currentAddCateg:'',
            product_ids:[],
        });
        self = this;
        self.state.family_id = this.props.record.resId;
        self.getCategories();
        onWillStart(async () => {
        });
        onWillUpdateProps(async (nextProps) => {
        });
    }

    async getCategories(){
        var jstreeData = await this.orm.call('pim.category', "return_categories_hierarchy", []);
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
//            if (!this.state.currentAddCateg){
//                if (ul) {
//                      const newLi = document.createElement("li");
//                      newLi.classList.add("my-class");
//                      const input = document.createElement("input");
//                      input.type = "text";
//                      input.placeholder = "Enter text";
//                      newLi.id = "my-id";
//                      newLi.appendChild(input);
//                      ul.appendChild(newLi);
//                    }
//                    this.state.currentAddCateg = categ_id;
//           }
//           else{
                const liToMove = document.querySelector(".my-class");
                if (liToMove && ul) {
                  ul.appendChild(liToMove);
                }
//                this.state.currentAddCateg = categ_id;
//
//           }

            this.state.addMode = true;
       }
    }

    async _viewSelectCatgeory(ev){
           console.log("before save ===== ",this.props.record.resId)
           await this.props.record.save();
           if(this.props.record.resId){
               if (!this.state.family_id){
                   this.state.family_id = this.props.record.resId;
               }
               let recordId = this.props.record.resId;
               let title = 'Select a Category';
               let existingCatList = this.state.existing_categ;
               let taxonomies = this.state.taxonomies;
               const addDialogProps = {
                    title,
                    recordId,
                    existingCatList,
                    taxonomies,
                    addCategory: (category) => this.addCategory(category),
                };
                this.dialogService.add(CategoryHierarchyDialog, addDialogProps);
           }
      }

    async addCategory(data){
     const category = data['category'];
     console.log("category ", category)
    //         this.state.taxonomies = await self.orm.searchRead("pim.category", [],  ["id","is_primary","family_category_id"]);
    //         self.state.existing_categ.push(category);
    //         console.log("self.state.existing_categ",self.state.existing_categ)
    //         if (self.state.primary_tax.length==0){
    //            const existing_categ = await self.orm.searchRead("family.attribute", [['id','=',self.state.family_id]],  ["primary_category_id","primary_taxonomy_id"]);
    //            self.state.primary_categ = existing_categ[0].primary_category_id[0];
    //            self.state.primary_tax = existing_categ[0].primary_taxonomy_id[0];
    //         }
    }

    async onRemoveTax(taxonomy_id){
    console.log("remove function",taxonomy_id,self,self.state.family_id)
    const result = await self.orm.call('family.attribute','remove_taxonomy', [self.state.family_id,taxonomy_id]);
    const rem_tax_line = self.state.taxonomies.findIndex(({ id }) => id === Number(taxonomy_id));
    self.state.taxonomies.splice(rem_tax_line, 1);
    self.state.existing_categ = result;
    console.log("existing_categ",self.state.existing_categ)
    }

    async MakePrimary(taxonomy_id){
    console.log("this.state.family_id",self.state.family_id,)
    await self.orm.call('family.attribute','make_primary', [self.state.family_id,taxonomy_id]);
    self.state.primary_tax = taxonomy_id;
    }


    async updateCategory(resId, products) {
        console.log("this  -- ",this)
        console.log("this  -- ",this.state.product_ids)
        console.log("resid -- ",resId)
        console.log("products  --- ",products)
        var category_update = await this.orm.call('category.wizard', "update_category", [1, resId, this.state.product_ids]);
        console.log("category_update == ", category_update)

    }

}
export const EnhancedCategoryWidget = {
    component: enhancedCategorywidget,
};
registry.category("fields").add("category_widget", EnhancedCategoryWidget);
