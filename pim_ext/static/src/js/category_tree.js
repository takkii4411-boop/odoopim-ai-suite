/** @odoo-module */

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";

// --- Shared Logic Mixin ---
const CategoryTreeMixin = {
    setupTreeState() {
        let expandedSet = new Set();
        let highlightedId = null;
        let pendingParentId = null;
        let shouldAutoRefresh = false;

        try {
            const stored = sessionStorage.getItem('pim_category_expanded');
            if (stored) {
                expandedSet = new Set(JSON.parse(stored));
            }

            const creatingForParent = sessionStorage.getItem('pim_category_creating_for_parent');
            const parentWasHighlighted = sessionStorage.getItem('pim_category_parent_highlighted');

            if (creatingForParent) {
                pendingParentId = parseInt(creatingForParent);
                shouldAutoRefresh = true;

                const currentPath = window.location.pathname;
                const pathMatch = currentPath.match(/\/pim\.category\/(\d+)/);

                if (pathMatch && !currentPath.includes('/new')) {
                    const newCategoryId = parseInt(pathMatch[1]);
                    highlightedId = newCategoryId;

                    sessionStorage.removeItem('pim_category_creating_for_parent');
                    sessionStorage.removeItem('pim_category_parent_highlighted');
                    sessionStorage.setItem('pim_category_just_created', newCategoryId);
                } else if (parentWasHighlighted) {
                    highlightedId = parseInt(parentWasHighlighted);
                }
            }

            const justCreated = sessionStorage.getItem('pim_category_just_created');
            if (justCreated) {
                highlightedId = parseInt(justCreated);
                sessionStorage.removeItem('pim_category_just_created');
            }
        } catch (e) {
            // storage error ignored
        }

        return {
            treeData: [],
            expanded: expandedSet,
            highlightedId: highlightedId,
            pendingParentId: pendingParentId,
            shouldAutoRefresh: shouldAutoRefresh,
            selectedCategoryId: null,
        };
    },

    buildTree(flatList) {
        if (!flatList?.length) return [];

        const map = {};
        const roots = [];

        flatList.forEach(item => {
            if (item.id) {
                map[item.id] = { 
                    ...item, 
                    children: [],
                    name: item.name || 'Unnamed Category',
                    id: item.id
                };
            }
        });

        flatList.forEach(item => {
            if (!item.id) return;
            
            const parent = item.parent_id?.[0];
            if (parent && map[parent]) {
                map[parent].children.push(map[item.id]);
            } else {
                roots.push(map[item.id]);
            }
        });

        return roots;
    },

    expandParents(currentId, allCats, expandedSet) {
        const cat = allCats.find(c => c.id === currentId);
        if (cat?.parent_id?.[0]) {
            expandedSet.add(cat.parent_id[0]);
            CategoryTreeMixin.expandParents(cat.parent_id[0], allCats, expandedSet);
        }
    },

    toggleExpand(nodeId, event) {
        if (event) event.stopPropagation();
        
        const { expanded } = this.state;
        if (expanded.has(nodeId)) {
            expanded.delete(nodeId);
        } else {
            expanded.add(nodeId);
        }

        sessionStorage.setItem('pim_category_expanded', JSON.stringify([...expanded]));
    },

    async onCategoryClick(nodeId, event) {
        if (event) event.stopPropagation();
        this.state.selectedCategoryId = nodeId;

        await this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'pim.category',
            res_id: nodeId,
            views: [[false, 'form']],
            target: 'current'
        });
    },

    async createChild(parentId, event) {
        if (event) event.stopPropagation();
        
        if (this.state && this.state.expanded) {
            this.state.expanded.add(parentId);
            this.state.highlightedId = parentId;

            sessionStorage.setItem('pim_category_expanded', JSON.stringify([...this.state.expanded]));
            sessionStorage.setItem('pim_category_creating_for_parent', parentId);
            sessionStorage.setItem('pim_category_parent_highlighted', parentId);
        }

        await this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'pim.category',
            view_mode: 'form',
            views: [[false, 'form']],
            context: { default_parent_id: parentId },
            target: 'current'
        });
    },

    async createCategory() {
        try {
            const result = await this.orm.call(
                'pim.category',
                'create_pim_category',
                [[]]
            );
            
            if (result?.type) {
                if (!result.views) result.views = [[false, 'form']];
                await this.action.doAction(result);
            }
        } catch (error) {
            this.notification.add('Failed to create category', { type: 'danger' });
        }
    },

    async editCategory(nodeId, event) {
        if (event) event.stopPropagation();
        this.state.selectedCategoryId = nodeId;

        try {
            const result = await this.orm.call(
                'pim.category',
                'category_edit_open_form_view',
                [[nodeId]]
            );
            
            if (result?.type) {
                if (!result.views) result.views = [[false, 'form']];
                await this.action.doAction(result);
            }
        } catch (error) {
            this.notification.add('Failed to open category', { type: 'danger' });
        }
    },

    async deleteCategory(nodeId, event) {
        if (event) event.stopPropagation();
        
        try {
            const result = await this.orm.call(
                'pim.category',
                'category_master_unlink',
                [[nodeId]]
            );
            
            if (result?.type) {
                if (!result.views) result.views = [[false, 'form']];
                await this.action.doAction(result);
            }
        } catch (error) {
            this.notification.add('Failed to delete category', { type: 'danger' });
        }
    }
};

// --- Component 1: Field Widget (Tree Nav) ---
class CategoryTreeNav extends Component {
    static template = "pim_ext.CategoryTreeNav";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.companyService = useService("company");
        this.notification = useService("notification");

        this.state = useState(CategoryTreeMixin.setupTreeState());

        onWillStart(() => this.loadData());

        onWillUpdateProps((nextProps) => {
            if (nextProps.record?.resId) {
                this.state.selectedCategoryId = nextProps.record.resId;
            } else {
                this.state.selectedCategoryId = null;
            }
        });
    }

    async loadData() {
        const currentCompanyId = this.companyService.currentCompany.id;
        const domain = [
            '|', 
            ['company_id', '=', false], 
            ['company_id', '=', currentCompanyId]
        ];

        try {
            const categories = await this.orm.searchRead(
                "pim.category", 
                domain, 
                ["id", "name", "parent_id"]
            );

            const validCategories = categories.filter(cat => cat.id);
            this.state.treeData = CategoryTreeMixin.buildTree(validCategories);

            if (this.props.record?.resId) {
                this.state.selectedCategoryId = this.props.record.resId;
                CategoryTreeMixin.expandParents(
                    this.props.record.resId, 
                    validCategories, 
                    this.state.expanded
                );
            }
        } catch (error) {
            this.state.treeData = [];
        }
    }

    // Bind methods
    toggleExpand(nodeId, event) { CategoryTreeMixin.toggleExpand.call(this, nodeId, event); }
    onCategoryClick(nodeId, event) { CategoryTreeMixin.onCategoryClick.call(this, nodeId, event); }
    createChild(parentId, event) { CategoryTreeMixin.createChild.call(this, parentId, event); }
    editCategory(nodeId, event) { CategoryTreeMixin.editCategory.call(this, nodeId, event); }
    deleteCategory(nodeId, event) { CategoryTreeMixin.deleteCategory.call(this, nodeId, event); }
}

// --- Component 2: List Renderer ---
export class CategoryListRenderer extends ListRenderer {
    static template = "pim_ext.CategoryListRenderer";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.companyService = useService("company");
        this.notification = useService("notification");

        this.state = useState(CategoryTreeMixin.setupTreeState());

        onWillStart(() => this.loadTreeData());

        if (this.state.shouldAutoRefresh) {
            this.startAutoRefresh();
        }

        this.env.bus.addEventListener('ACTION_MANAGER:UPDATE', this.onActionUpdate.bind(this));

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.list !== this.props.list) {
                await this.loadTreeData();
            }
        });
    }

    startAutoRefresh() {
        let attempts = 0;
        const maxAttempts = 10;

        const checkInterval = setInterval(async () => {
            attempts++;
            if (attempts > maxAttempts) {
                clearInterval(checkInterval);
                this.state.shouldAutoRefresh = false;
                return;
            }

            await this.loadTreeData();

            if (this.state.highlightedId && !this.state.pendingParentId) {
                clearInterval(checkInterval);
                this.state.shouldAutoRefresh = false;
            }
        }, 500);
    }

    async onActionUpdate(event) {
        if (event.detail?.action?.res_model === 'pim.category') {
            await this.loadTreeData();
        }
    }

    async loadTreeData() {
        try {
            const currentCompanyId = this.companyService.currentCompany.id;
            const domain = [
                '|',
                ['company_id', '=', false],
                ['company_id', '=', currentCompanyId]
            ];

            const allCategories = await this.orm.searchRead(
                "pim.category",
                domain,
                ["id", "name", "parent_id", "code"],
                { order: 'id desc' }
            );

            // Handle pending parent (Child Creation Highlight Logic)
            if (this.state.pendingParentId) {
                const parentId = this.state.pendingParentId;
                const childrenOfParent = allCategories.filter(cat =>
                    cat.parent_id && cat.parent_id[0] === parentId
                );

                if (childrenOfParent.length > 0) {
                    const newestChild = childrenOfParent[0];
                    this.state.highlightedId = newestChild.id;
                    this.state.pendingParentId = null;
                    this.state.expanded.add(parentId);

                    sessionStorage.removeItem('pim_category_creating_for_parent');
                    sessionStorage.removeItem('pim_category_parent_highlighted');

                    setTimeout(() => {
                        if (this.state.highlightedId === newestChild.id) {
                            this.state.highlightedId = null;
                        }
                    }, 3000);
                }
            }

            const validCategories = allCategories.filter(cat => !!cat.id);
            this.state.treeData = CategoryTreeMixin.buildTree(validCategories);
        } catch (error) {
            this.state.treeData = [];
        }
    }

    // Bind methods
    toggleExpand(nodeId, event) { CategoryTreeMixin.toggleExpand.call(this, nodeId, event); }
    createCategory() { CategoryTreeMixin.createCategory.call(this); }
    createChild(parentId, event) { CategoryTreeMixin.createChild.call(this, parentId, event); }
    editCategory(nodeId, event) { CategoryTreeMixin.editCategory.call(this, nodeId, event); }
    deleteCategory(nodeId, event) { CategoryTreeMixin.deleteCategory.call(this, nodeId, event); }
    async onCategoryClick(nodeId, event) { await CategoryTreeMixin.onCategoryClick.call(this, nodeId, event); }
}

// --- Registries ---
export const categoryTreeNav = {
    component: CategoryTreeNav,
    supportedTypes: ["char", "many2one"]
};

registry.category("fields").add("category_tree_nav", categoryTreeNav);

export const categoryListView = {
    ...listView,
    Renderer: CategoryListRenderer,
};

registry.category("views").add("category_list_view", categoryListView);
