# -*- coding: utf-8 -*-

from odoo import fields, models


class change_prm_category(models.TransientModel):
    """
    The wizard for mass action to update product category
    """
    _name = "change.prm.category"
    _inherit = "product.sample.wizard"
    _description = "Update Category"

    category_id = fields.Many2one("product.category", string="New category", required=True)

    def _update_products(self, product_ids):
        """
        The method to write category to a product

        Args:
         * product_ids - product.template recordset
        """
        product_ids.write({"categ_id": self.category_id.id})
