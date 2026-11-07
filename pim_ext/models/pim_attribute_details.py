# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AttributeDetails(models.Model):
    _name = 'attribute.details'
    _description = 'Attribute Details'

    name = fields.Char(string="Label")
    code = fields.Char(string="Code")
    attribute_id = fields.Many2one('pim.attribute.attribute', string='Attribute main page')
    type = fields.Char(string='Attribute Type')

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.code = self.name.replace(' ', '_')

    def action_confirm(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.attribute',  # Change this to your target model
            'view_mode': 'form',
            # 'res_id': self.id,  # This could be the ID of another record if needed
            'target': 'current',  # Opens in the same window
        }


    def action_cancel(self):
        print('dkjfdkfj')
        # Logic to execute on cancel (e.g., just close the form)
        # return {
        #     'type': 'ir.actions.act_window_close',
        # }

