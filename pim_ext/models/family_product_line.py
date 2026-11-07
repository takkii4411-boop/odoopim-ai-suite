# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FamilyProductsLine(models.Model):
    _name = 'family.products.line'
    _description = 'Family Product'
    # _sql_constraints = [
    #     ('uniq_product', 'unique(id, product_id)',
    #      "SKU should be unique!"),
    # ]

    product_id = fields.Many2one('product.template', 'SKU Name')
    attribute_id = fields.Many2one('product.attribute', string='Attribute')
    attribute_group_id = fields.Many2one('attribute.group', string='Attribute Group')
    # name = fields.Char('SKU Name')
    # default_code = fields.Integer('SKU #', default=lambda self: self.env['ir.sequence'].next_by_code('family.products'))
    families_id = fields.Many2one('family.attribute', 'Family')
    completeness_percent = fields.Float(compute="_compute_completeness_percent", string="Completeness")

    product_id_stored = fields.Integer(string="SKU #", compute='_compute_product_id')

    @api.depends('product_id')
    def _compute_product_id(self):
        for record in self:
            if record.product_id:
                record.product_id_stored = record.product_id.id
            else:
                record.product_id_stored = False

    def _compute_completeness_percent(self):
        for rec in self:
            # required_family_fields = ['name', 'brand_id', 'supplier_id', 'manufacture_id', 'buyer_id', 'description',
            #                           'availability', 'gift', 'swatch', 'attribute1_id', 'attribute2_id', 'attribute3_id']
            # required_sku_fields = (rec.family_id.attribute_group_selection.used_attribute_ids.filtered(lambda x: x.completeness)
            #                        + rec.family_id.add_attribute_fields.filtered(lambda x: x.completeness)).mapped('original_name')
            # filled_count = 0
            # for field in required_family_fields:
            #     if getattr(rec.family_id, field):
            #         filled_count += 1
            # for field in required_sku_fields:
            #     if getattr(rec, field):
            #         filled_count += 1
            # if required_sku_fields:
            #     rec.completeness_percent = filled_count/len(required_sku_fields)*100
            # else:
                rec.completeness_percent = 100