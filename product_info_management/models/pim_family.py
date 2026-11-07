# -*- coding: utf-8 -*-
from odoo import fields, models


class PIMFamily(models.Model):
    _name = "pim.family"
    _description = "PIM Families"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", size=128, required=True, translate=True)