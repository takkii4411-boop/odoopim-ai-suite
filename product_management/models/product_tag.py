#coding: utf-8

from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class product_tag(models.Model):
    """
    Re-write to implement methods needed by js interface
    """
    _inherit = "product.tag"

    @api.model
    def _return_tags_hierarchy(self):
        """
        The method to return tags in jstree format

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
        """
        res = []
        Config = self.env["ir.config_parameter"].sudo()
        need_tags = safe_eval(Config.get_param("product_management_tags_option", "False"))
        if need_tags:
            tags = self.search([])
            for tag in tags:
                res.append({"id": tag.id, "text": tag.name})
        return res
