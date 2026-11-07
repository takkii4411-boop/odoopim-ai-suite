# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class update_prm_optional_products(models.TransientModel):
    """
    The wizard for mass action to add or/and remove attribute value
    """
    _name = "update.prm.optional.products"
    _inherit = "product.sample.wizard"
    _description = "Update optional products"

    optioanl_to_add_ids = fields.Many2many(
        "product.template",
        "product_template_update_prm_optional_products_rel_table",
        "product_template_id",
        "update_prm_optional_products_id",
        string="Add optional products",
    )
    optional_to_exclude_ids = fields.Many2many(
        "product.template",
        "product_template_exclude_update_prm_optional_products_rel_table",
        "product_template_id",
        "update_prm_optional_products_id",
        string="Remove optional products",
    )

    def _update_products(self, product_ids):
        """
        The method to prepare new vals for public categories

        Args:
         * product_ids - product.template recordset
        """
        if not hasattr(self.env["product.template"], "optional_product_ids"):
            raise ValidationError(
                _("The module Sale Product Configurator is not installed. Products can not have optional products")
            )
        if self.optioanl_to_add_ids:
            to_add = []
            for alter in self.optioanl_to_add_ids.ids:
                to_add.append((4, alter))
            product_ids.write({"optional_product_ids": to_add,})
        if self.optional_to_exclude_ids:
            to_exclude = []
            for alter in self.optional_to_exclude_ids.ids:
                to_exclude.append((3, alter))
            product_ids.write({"optional_product_ids": to_exclude,})
