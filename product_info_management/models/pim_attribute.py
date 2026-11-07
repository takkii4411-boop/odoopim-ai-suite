# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PIMAttribute(models.Model):
    _name = 'pim.attribute'
    _description = 'PIM Attributes'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    attribute_type = fields.Selection(
        [
            ("char", "Char"),
            ("text", "Text"),
            ("select", "Select"),
            ("multiselect", "Multiselect"),
            ("color", "Color"),
            ("monetary", "Monetary"),
            ("boolean", "Boolean"),
            ("integer", "Integer"),
            ("date", "Date"),
            ("datetime", "Datetime"),
            ("binary", "Binary"),
            ("float", "Float"),
        ],
    )

    name = fields.Char(string='Label', size=100, help="Name of the attribute")
    code = fields.Char('Code', size=255, required=True, help="Code for the attribute")

    attribute_group_id = fields.Many2one(
        "pim.attribute.group", "Attribute Groups", required=True, ondelete="cascade"
    )

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.code = self.name.replace(' ', '_')
