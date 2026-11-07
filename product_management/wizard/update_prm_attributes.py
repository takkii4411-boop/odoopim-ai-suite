# -*- coding: utf-8 -*-

from odoo import fields, models


class update_prm_attributes(models.TransientModel):
    """
    The wizard for mass action to add or/and remove attribute value
    """
    _name = "update.prm.attributes"
    _inherit = "product.sample.wizard"
    _description = "Update attributes"

    values_to_add_id = fields.Many2one("product.attribute.value", string="Add attribute value")
    values_to_exclude_id = fields.Many2one("product.attribute.value", string="Remove attribute value")

    def _update_products(self, product_ids):
        """
        The method to prepare new vals for attributes

        Args:
         * product_ids - product.template recordset

        Extra info:
         * Here we can't write in self, since for certain products there would be no such attribute line
        """
        for product in product_ids:
            update = []
            if self.values_to_add_id:
                value = self.values_to_add_id
                ex_attr = product.attribute_line_ids.filtered(lambda line: line.attribute_id == value.attribute_id)
                if ex_attr:
                    if value not in ex_attr.value_ids:
                        update.append((1, ex_attr.id, {"value_ids": [(4, value.id)]}))
                else:
                    update.append((0, 0, {
                        "attribute_id": value.attribute_id.id,
                        "value_ids": [(4, value.id)],
                    }))
            if self.values_to_exclude_id:
                value = self.values_to_exclude_id
                ex_attr = product.attribute_line_ids.filtered(lambda line: line.attribute_id == value.attribute_id)
                if ex_attr and value in ex_attr.value_ids:
                    if len(ex_attr.value_ids) == 1:
                        ex_attr.unlink()
                    else:
                        update.append((1, ex_attr.id, {"value_ids": [(3, value.id)]}))
            product.write({"attribute_line_ids": update,})
