# -*- coding: utf-8 -*-
from odoo import fields, models


class PIMAttributeGroup(models.Model):
    _name = "pim.attribute.group"
    _description = "PIM Attributes Group"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", size=128, required=True, translate=True)