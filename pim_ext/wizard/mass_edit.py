# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
import ast

class ProductValSelect(models.TransientModel):
    _name = 'product.val.select'
    _description = 'Product Value Update'
    
    fieldname = fields.Many2one('ir.model.fields','Field Name',required=True,domain="[('name','in',('mpn_number','status','origin','po_min','po_max','p65','attribute1_id','attribute2_id','attribute3_id','attribute4_id')),('model','=','product.template')]")
    field_value = fields.Char('Value')
    select_id = fields.Many2one('product.multi.select','Mass Select',required=True)
    
class ProductMultiSelect(models.TransientModel):
    _name = 'product.multi.select'
    _description = 'Update Multiple Products'
    
    # attribute1_id = fields.Many2one('product.attribute1','Attribute 1')
    attribute1_val = fields.Char('Value 1')
    # attribute2_id = fields.Many2one('product.attribute2','Attribute 2')
    attribute2_val = fields.Char('Value 2')
    # attribute3_id = fields.Many2one('product.attribute3','Attribute 3')
    attribute3_val = fields.Char('Value 3')
    # attribute4_id = fields.Many2one('product.attribute4','Attribute 4')
    attribute4_val = fields.Char('Value 4')
    mpn_number = fields.Char('MPN')
    status = fields.Selection([('active','Active'),('inactive','In Active')],'Status')
    origin = fields.Char('Origin')
    po_min = fields.Integer('PO Min')
    po_max = fields.Integer('PO Max')
    p65 = fields.Char('P65')
    default_code = fields.Char('SKU #')
    val_id = fields.One2many('product.val.select','select_id','Update Value')

    def update_products(self):
        res = []
        active_id = self.env.context.get('active_ids')
        products_obj = self.env['family.products']
        prod_vals = []
        for record in self.val_id:
            if record.fieldname.name == 'attribute1_id':
                field_name = 'attribute1_val'
                val = [field_name,'*',record.field_value]
            if record.fieldname.name == 'attribute2_id':
                field_name = 'attribute2_val'
                val = [field_name,'*',record.field_value]
            if record.fieldname.name == 'attribute3_id':
                field_name = 'attribute3_val'
                val = [field_name,'*',record.field_value]
            if record.fieldname.name == 'attribute4_id':
                field_name = 'attribute4_val'
                val = [field_name,'*',record.field_value]
            if record.fieldname.name in ('status','origin','po_min','po_max','p65','mpn_number','default_code'):
                val = [record.fieldname.name,'*',record.field_value]
            prod_vals.append(val)
        dict_val = str(prod_vals).replace('[', '').replace(']', '')
        dict_replace = str(dict_val).replace(", '*', ",":").replace(", '*', ",":")
        final_dict = '{'+dict_replace+'}'
        my_dict = ast.literal_eval(final_dict)
        product_search = products_obj.search([('select_sku','=',True),('family_id','=',active_id[0])])
        for families in product_search:
            families.write(my_dict)
            product_search.write({'select_sku':False})
        return res

