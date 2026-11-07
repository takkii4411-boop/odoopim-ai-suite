from odoo import models, api, fields, _

class PimCategory(models.Model):
    """
    Re-write to implement methods needed by js interface
    """
    _inherit = "pim.category"

    @api.model
    def return_categories_hierarchy(self):
        """
        The method to return categories in jstree format

        Methods:
         * _return_categories_recursive

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
           ** children - array with the same keys
        """
        print("vreturn_categories_hierarchy  ================ ",self)
        categories = self.search([("parent_id", "=", False)])
        res = []
        for category in categories:
            print("category == ", category)
            res.append(category.return_categories_recursive())
        print("jhkbdgowu ", res)
        return res

    def return_categories_recursive(self):
        """
        The method to go by all categories recursively to prepare their list in js_tree format

        Extra info:
         * Expected singleton
        """
        print("return_categories_recursive ===========")
        res = {"id": self.id, "text": self.name}
        child_res = []
        child_ids = self.search([("id", "in", self.child_ids.ids)])
        for child in child_ids:
            child_res.append(child.return_categories_recursive())
        res.update({"children": child_res})
        return res

    # def _return_categories_recursive(self):
    #     """
    #     The method to go by all categories recursively to prepare their list in js_tree format
    #
    #     Extra info:
    #      * Expected singleton
    #     """
    #     print("_return_categories_recursive == ")
    #     res = {"id": self.id, "text": self.name}
    #     child_res = []
    #     child_ids = self.search([("id", "in", self.child_id.ids)])
    #     for child in child_ids:
    #         print("child  -------- ", child)
    #         child_res.append(child._return_categories_recursive())
    #     res.update({"children": child_res})
    #     return res


class FamilyAttribute(models.Model):
    _inherit = 'family.attribute'

    @api.model
    def action_get_hierarchy(self, key):
        """
        The method to prepare hierarchy

        Args:
         * key - string - js tree reference

        Methods:
         * _return_categories_hierarchy of product.category
         * _return_attributes_and_values of product.attribute
         * _return_eshop_categories_hierarchy of product template
         * _return_tags_hierarchy of product.tag

        Returns:
         * list of dicts
        """
        result = []
        if key == "categories":
            result = self.env["family.category"]._return_categories_hierarchy()
        # elif key == "attributes":
        #     result = self.env["product.attribute"]._return_attributes_and_values()
        # elif key == "eshop_categories":
        #     result = self.env["product.template"]._return_eshop_categories_hierarchy()
        # elif key == "product_tags":
        #     result = self.env["product.tag"]._return_tags_hierarchy()
        return result
