# -*- coding: utf-8 -*-

from odoo import fields, models


class update_prm_price(models.TransientModel):
    """
    The wizard for mass action to update list_price
    """
    _name = "update.prm.price"
    _inherit = "product.sample.wizard"
    _description = "Update Sales Price"

    price = fields.Float("Sales Price", required=True)

    def _update_products(self, product_ids):
        """
        The method write sale price

        Args:
         * product_ids - product.template recordset
        """
        product_ids.write({"list_price": self.price})
