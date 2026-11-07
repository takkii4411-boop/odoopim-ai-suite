# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

class ProductSelect(models.TransientModel):
    _name = 'product.select'
    _description = 'Add products into family'
    
    product_ids = fields.Many2many('product.template', string="Select Products")
    
    def add_sku(self):
        res = []
        active_id = self.env.context.get('active_ids')
        products_obj = self.env['family.products']
        for record in self.product_ids:
            product_search = products_obj.search([('product_id','=',record.id),('family_id','=',active_id[0])])
            if product_search:
                raise ValidationError(_("This product has been already already - %(name)s.",name=record.name))
            res = products_obj.create({
                'product_id': record.id,
                'default_code': record.default_code,
                'family_id': active_id[0],
                'mpn_number': record.mpn_number,
                'status': record.status,
                'origin': record.origin,
                'po_min': record.po_min,
                'po_max': record.po_max,
                'p65': record.p65,
                'attribute1_id': record.attribute1_id.id,
                'attribute1_val': record.attribute1_val,
                'attribute2_id': record.attribute2_id.id,
                'attribute2_val': record.attribute2_val,
                'attribute3_id': record.attribute3_id.id,
                'attribute3_val': record.attribute3_val,
                'attribute4_id': record.attribute4_id.id,
                'attribute4_val': record.attribute4_val,
                })
            
        return res

