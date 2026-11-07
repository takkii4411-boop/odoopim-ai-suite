# -*- coding: utf-8 -*-

from odoo import Command, fields, models


class copy_values_from_template(models.TransientModel):
    """
    The wizard for mass action to update product category
    """
    _name = "copy.values.from.template"
    _inherit = "product.sample.wizard"
    _description = "Copy Values"

    master_id = fields.Many2one("product.template", string="Master Product", required=True)
    ir_model_field_ids = fields.Many2many(
        "ir.model.fields",
        string="Fields to copy",
        domain=[
            ("model", "=", "product.template"), ("store", "=", True), ("related", "=", False), ("compute", "=", False)
        ],
        required=True,
    )

    def _update_products(self, product_ids):
        """
        The method to write category to a product

        Args:
         * product_ids - product.template recordset
        """
        product_ids = product_ids - self.master_id
        values, o2m_values = {}, {}
        for field in self.ir_model_field_ids:
            name = field.name
            if field.ttype == "one2many":
                lines = [rec.copy_data()[0] for rec in self.master_id[name].sorted(key="id")]
                o2m_values.update({name: False})
                values.update({name: [Command.create(line) for line in lines if line]})
            elif field.ttype == "many2many":
                values.update({name: [Command.set(self.master_id[name].ids)]})
            else:
                values.update({name: self.master_id[name]})
        if o2m_values:
            # to remove old o2m values
            product_ids.write(o2m_values)
        if values:
            product_ids.write(values)
