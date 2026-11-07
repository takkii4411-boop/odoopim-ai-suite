#coding: utf-8

from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class product_attribute(models.Model):
    """
    Re-write to implement methods needed by js interface
    """
    _inherit = "product.attribute"

    @api.model
    def _return_attributes_and_values(self):
        """
        The method to return attributes and values in jstree format
        Here we have only 2 levels: (1) attribute, (2) its possible values

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
           ** children - array with the same keys
        """
        Config = self.env["ir.config_parameter"].sudo()
        need_attributes = safe_eval(Config.get_param("product_management_attributes_option", "False"))
        res = []
        if need_attributes:
            all_attributes = self.search([])
            for attribute in all_attributes:
                child_res = []
                for value in attribute.value_ids:
                    child_res.append({"id": value.id, "text": value.name})
                res.append({
                    "text": attribute.name,
                    "id": "product_attribute_{}".format(attribute.id), # to make sure id is unique
                    "children": child_res,
                })
        return res
