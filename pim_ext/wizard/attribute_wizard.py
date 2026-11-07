# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AddAttributeWizard(models.TransientModel):
    _name = 'add.attribute.wizard'
    _description = 'Attribute Wizard'

    attribute_ids = fields.Many2many('product.attribute', string='Attributes', required=True)
    attribute_family_id = fields.Many2one('family.attribute', string='Families')
    exist_attribute_ids = fields.Many2many('product.attribute', related='attribute_family_id.exist_attribute_ids')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def add_attributes_to_family(self):
        family = self.attribute_family_id
        group = self.env['attribute.group'].search([('company_id', '=', self.env.company.id),
                                                    ('name', '=ilike', 'Default')])
        for attribute in self.attribute_ids:
            family.write({
                'family_attribute_ids': [(0, 0, {
                    'attribute_id': attribute.id,
                    'attribute_group_id': group.id,
                })]
            })
