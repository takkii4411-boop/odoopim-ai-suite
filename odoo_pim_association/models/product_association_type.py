# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductAssociationType(models.Model):
    _name = 'product.association.type'
    _description = 'Product Association Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description', translate=True)
    color = fields.Integer(string='Color Index', default=0)
    company_id = fields.Many2one('res.company', string='Company')

    _sql_constraints = [
        ('code_uniq', 'unique(code, company_id)', 'Association type code must be unique per company!')
    ]


class ProductAssociation(models.Model):
    _name = 'product.association'
    _description = 'Product Association - One Record Per Product Per Type'
    _order = 'sequence, id'

    product_id = fields.Many2one('product.template', string='Product', required=True, ondelete='cascade')
    association_type_id = fields.Many2one('product.association.type', string='Association Type', required=True)
    associated_product_ids = fields.Json(string='Associated Products', default=[])
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Company', related='product_id.company_id', store=True)

    _sql_constraints = [
        ('unique_product_type', 'unique(product_id, association_type_id)',
         'Only one association record per product per type!')
    ]

    def get_associated_products(self):
        """Helper to get associated product records"""
        self.ensure_one()
        if not self.associated_product_ids:
            return self.env['product.template']
        return self.env['product.template'].browse(self.associated_product_ids)

