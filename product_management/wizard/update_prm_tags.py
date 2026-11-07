# -*- coding: utf-8 -*-

from odoo import fields, models


class update_prm_tags(models.TransientModel):
    """
    The wizard for mass action to add/remove tags
    """
    _name = "update.prm.tags"
    _inherit = "product.sample.wizard"
    _description = "Update product tags"

    tag_add_ids = fields.Many2many(
        "product.tag",
        "product_tag_update_prm_tags_rel_table",
        "product_tag_id",
        "uupdate_prm_tags_id",
        string="Add tags",
    )
    tag_to_exclude_ids = fields.Many2many(
        "product.tag",
        "product_tag_update_prm_tags_rel_exclde_table",
        "product_tag_id",
        "update_prm_tags_id",
        string="Remove tags",
    )

    def _update_products(self, product_ids):
        """
        The method to prepare new vals for tags

        Args:
         * product_ids - product.template recordset
        """
        if self.tag_add_ids:
            to_add = []
            for tag in self.tag_add_ids.ids:
                to_add.append((4, tag))
            product_ids.write({"product_tag_ids": to_add})
        if self.tag_to_exclude_ids:
            to_exclude = []
            for tag in self.tag_to_exclude_ids.ids:
                to_exclude.append((3, tag))
            product_ids.write({"product_tag_ids": to_exclude})
