/** @odoo-module **/

import { Domain } from "@web/core/domain";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted, useState } = owl;

const componentModel = "product.template";


export class JsTreeContainer extends Component {
    static template = "product_management.jsTreeContainer";
    static props = {
        jstreeTitle: { type: String },
        jstreeId: { type: String },
        onUpdateSearch: { type: Function },
    };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.state = useState({ treeData: null });
        this.orm = useService("orm");
        this.searchString = "";
        onWillStart(async () => { await this._loadTreeData(this.props) });
        onMounted(() => {
            this.jsTreeAnchor = $("#"+this.id);
            this.jsTreeSearchInput = $("#jstr_input_" + this.id)[0];
            this._renderJsTree();
        })
    }
    /*
    * Getter for title
    */
    get title() {
        return this.props.jstreeTitle;
    }
    /*
    * Getter for id (jstree_key unique reference)
    */
    get id() {
        return this.props.jstreeId;
    }
    /*
    * The method to update jsTree data
    */
    async _loadTreeData() {
        var jstreeData = await this.orm.call(componentModel, "action_get_hierarchy", [this.id]);
        if (jstreeData.length == 0) {
            jstreeData = null;
        };
        Object.assign(this.state, { treeData: jstreeData });
    }
    /*
    * The method to initiate jstree
    */
    async _renderJsTree() {
        if (!this.state.treeData) { return };
        var self = this;
        const jsTreeOptions = {
            "core" : {
                "themes": {"icons": false},
                "check_callback" : true,
                "data": this.state.treeData,
                "multiple" : true,
            },
            "plugins" : [
                "checkbox",
                "state",
                "search",
            ],
            "state" : { "key" : this.id },
            "checkbox" : {
                "three_state" : false,
                "cascade": "down",
                "tie_selection" : false,
            },
            "contextmenu": {
                "select_node": false,
            },
        };
        const jsTree = this.jsTreeAnchor.jstree(jsTreeOptions);
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        this.jsTreeAnchor.on("state_ready.jstree", self, function (event, data) {
            self._onUpdateDomain(jsTreeAnchor);
            self.jsTreeAnchor.on("check_node.jstree uncheck_node.jstree", self, function (event, data) {
                // We register "checks" only after restoring the tree to avoid multiple checked events
                self._onUpdateDomain(jsTreeAnchor);
            })
            self.jsTreeAnchor.on("open_node.jstree", self, function (event, data) {
                // On each opening we should recalculate highlighted parents
                self._highlightParent(jsTreeAnchor, jsTreeAnchor.get_checked(), "#"+self.id);
            })
        });
    }
    /*
    * The method to calculate domain based on checks and trigger the parent search model to reload
    * For 'attributes' we need the full node info since parents will be under check
    */
    _onUpdateDomain(jsTreeAnchor) {
        const checkedTreeItems = jsTreeAnchor.get_checked(this.id == "attributes");
        this._highlightParent(jsTreeAnchor, checkedTreeItems, "#"+this.id);
        this.props.onUpdateSearch(this.id, this._getDomain(checkedTreeItems));
    }
    /*
    * The method to uncheck all nodes in the tree
    */
    _onClearJsTree() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.uncheck_all();
        jsTreeAnchor.save_state();
        this._onUpdateDomain(jsTreeAnchor);
    }
    /*
    * The method to get change in the search input and save it
    */
    _onSearchChange(event) {
        this.searchString = event.currentTarget.value;
    }
    /*
    * The method to execute search in jsTree
    */
    _onSearchExecute() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.uncheck_all();
        if (this.searchString) {
            this.jsTreeAnchor.jstree("search", this.searchString);
        }
        else {
            this.jsTreeAnchor.jstree("clear_search");
        }
        this._onUpdateDomain(jsTreeAnchor); // so unchecked leaves are reflected
    }
    /*
     * The method to manage keyup on search input > if enter then make search
    */
    _onSearchkeyUp(event) {
        if (event.keyCode === 13) {
            this._onSearchExecute();
        };
    }
    /*
     * The method to clear seach input and clear jstree search
    */
    _onSearchClear() {
        this.jsTreeSearchInput.value = "";
        this.searchString = "";
        this.jsTreeAnchor.jstree("clear_search");
    }
    /*
    * The method to calculate domain based on JsTree values
    */
    _getDomain(checkedTreeItems) {
        if (this.id == "categories") {
            return this._getMany2OneDomain(checkedTreeItems, "categ_id");
        }
        else if (this.id == "attributes") {
            return this._getSpecialAttributesDomain(checkedTreeItems);
        }
        else if (this.id == "eshop_categories") {
            return this._getMany2ManyDomain(checkedTreeItems, "public_categ_ids")
        }
        else if (this.id == "product_tags") {
            return this._getMany2ManyDomain(checkedTreeItems, "product_tag_ids")
        };
        return []
    }
    /*
    * The method to prepare the domain for M2O 'in' domain
    */
    _getMany2OneDomain(checkedTreeItems, field) {
        const checkedIds = checkedTreeItems.map(function(checkedItem) {return parseInt(checkedItem)});
        if (checkedIds.length != 0) {
            return [[field, "in", checkedIds]];
        };
        return [];
    }
    /*
    * The method to prepare the domain for M2M 'in' domain
    */
    _getMany2ManyDomain(checkedTreeItems, field) {
        var domain = [];
        checkedTreeItems.forEach(function (checkedItem) {
            domain = Domain.or([domain, [[field, "in", parseInt(checkedItem)]]]).toList();
        });
        return domain;
    }
    /*
    * The method to prepare very special domain for product attributes and their values
    */
    _getSpecialAttributesDomain(checkedTreeItems) {
        var domain = [];
        const allCheckedParents = [... new Set(checkedTreeItems.map((rec) => rec.parent))];
        allCheckedParents.forEach(function (checkedParent) {
            if (checkedParent == "#") {
                // if attribute is selected it should be present in template
                checkedTreeItems.forEach(function (checkedItem) {
                    if (checkedItem.parent == checkedParent) {
                        var checkedItemId = checkedItem.id.replace("product_attribute_", "");
                        domain = Domain.and([
                            domain, [["attribute_to_search_ids", "in", parseInt(checkedItemId)]]
                        ]);
                    };
                });
            }
            else {
                // we combine different values of the same attribute with OR, of different - with AND
                var localDomain = [];
                checkedTreeItems.forEach(function (checkedItem) {
                    if (checkedItem.parent == checkedParent) {
                        localDomain = Domain.or([
                            localDomain, [["attribute_values_to_search_ids", "in", parseInt(checkedItem.id)]]
                        ]);
                    };
                });
                domain = Domain.and([domain, localDomain]);
            }
        });
        return domain;
    }
    /*
    * The method to highlight not selected parent nodes that have selected children
    * That's triggered when a node is selected or opened. The reason for the latter is that not loaded nodes get
    * class from state while we do not want to always iterate over those
    */
    _highlightParent(jsTreeAnchor, checkedNodes, jsSelector) {
        $(jsSelector + "* .jstr-selected-parent").removeClass("jstr-selected-parent");
        var allParentNodes = [];
        checkedNodes.forEach(function (node) {
            const thisNodeParents = jsTreeAnchor.get_path(node, false, true);
            allParentNodes = allParentNodes.concat(thisNodeParents);
        });
        allParentNodes = [... new Set(allParentNodes)];
        allParentNodes.forEach(function (nodeID) {
            $(jsSelector + " * .jstree-node#" + nodeID).addClass("jstr-selected-parent");
        });
    }
}
