# -*- coding: utf-8 -*-

from odoo import api, fields, models


class update_prm_product_type(models.TransientModel):
    """
    The wizard for mass action to add change product type
    """
    _name = "update.prm.product.type"
    _inherit = "product.sample.wizard"
    _description = "Update Product Type"

    @api.model
    def ttype_selection(self):
        """
        The method to return avaialble selection values for types (since it might depend on installed modules)
        """
        return self.env["product.template"]._fields["type"]._description_selection(self.env)

    ttype = fields.Selection(ttype_selection, string="New type")

    def _update_products(self, product_ids):
        """
        The method to prepare new vals type

        Args:
         * product_ids - product.template recordset
        """
        product_ids.write({"type": self.ttype})
