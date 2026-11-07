'''
Created on Jun 21, 2023

@author: Zuhair Hammadi
'''
from odoo import models, api

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def _validate_custom_views(self, model):
        if model =='base':
            self.env['ir.model.fields.attribute']._update_fields_attributes()
        return super(IrUiView, self)._validate_custom_views(model)
