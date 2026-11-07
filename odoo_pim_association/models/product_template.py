# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_association_ids = fields.One2many(
        'product.association',
        'product_id',
        string='Product Associations'
    )

    association_count = fields.Integer(
        string='Association Count',
        compute='_compute_association_count',
        store=False
    )

    @api.depends('product_association_ids',
                 'product_association_ids.associated_product_ids')
    def _compute_association_count(self):
        for record in self:
            total = 0
            for assoc in record.product_association_ids:
                if assoc.associated_product_ids:
                    total += len(assoc.associated_product_ids)
            record.association_count = total