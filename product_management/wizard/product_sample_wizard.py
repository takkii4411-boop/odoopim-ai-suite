# -*- coding: utf-8 -*-

from odoo import api, fields, models


class product_sample_wizard(models.TransientModel):
    """
    The wizard to be inherited in any update wizard that assumes writing mass values in templates
    """
    _name = "product.sample.wizard"
    _description = "Product Update"

    product_ids = fields.Many2many("product.template", string="Updated products")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to trigger products update
        The idea is to use standard 'Save' buttons and do not introduce its own footer for each mass action wizard

        Methods:
         * action_update_products
        """
        wizards = super(product_sample_wizard, self).create(vals_list)
        wizards.action_update_products()
        return wizards

    def action_update_products(self):
        """
        The method to update products in batch

        Methods:
         * _update_products
        """
        for wiz in self:
            if wiz.product_ids:
                wiz._update_products(wiz.product_ids)

    def _update_products(self, product_ids):
        """
        Dummy method to prepare values
        It is to be inherited in a real update wizard

        Args:
         * product_ids - product.template recordset
        """
        pass
