from datetime import datetime
from markupsafe import Markup
from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class FamilyWizard(models.TransientModel):
    _name = 'family.wizard'
    _description = "Family Wizard"

    family_id = fields.Many2one('family.attribute', 'Family')
    product_ids = fields.Many2many('product.template')


    def action_update(self):
        print("family -- action_update ===============")
        for rec in self:
            selected_family = rec.family_id.id
            print("selected_family === ", selected_family)
            if selected_family:
                for p in rec.product_ids:
                    p.family_id = selected_family




