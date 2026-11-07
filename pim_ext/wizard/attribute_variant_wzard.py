# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, AccessError


class AttributeVariantWizard(models.TransientModel):
    _name = 'attribute.variant.wizard'
    _description = 'Attribute Variant'

    name = fields.Char(string='Label')

    def _default_variant_domain(self):
        return [('display_type','in',['simple_select','color']),('company_id','in',[self.env.company.id])]

    variant_ids = fields.Many2many(
        'product.attribute',
        string='Variants',
        relation='custom_product_line_variant_rels',
        column1='custom_line_id',
        column2='variant_id',
        domain=_default_variant_domain
    )
    attribute_family_id = fields.Many2one('family.attribute', string='Families')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    # def add_attributes_variant_to_family(self):
    #     print('dkfodkf')
    #     family_id = self.attribute_family_id.id
    #     print('dw33333', family_id)
    #     family = self.env['family.attribute'].browse(family_id)
    #     print('22222222', family)
    #
    #     for variant in self.variant_ids:
    #         print('variantwwwwww', variant)
    #         family.write({
    #             'variant_line_ids': [(0, 0, {
    #                 'variant_id': variant.id,
    #             })]
    #         })

    def add_attributes_variant_to_family(self):
        print('dkfodkf')
        family_id = self.attribute_family_id.id
        print('Selected Family ID:', family_id)

        family = self.env['family.attribute'].browse(family_id)
        print('Family Record:', family)
        variants_to_add = [(4, variant.id) for variant in self.variant_ids]
        print('Variants to Add:', variants_to_add)
        family.write({
            'variant_line_ids': [(0, 0, {
                'name': self.name,
                'variant_ids': variants_to_add,
                'variant_family_id': family_id,
            })]
        })
        return True


class AttributeVariantValuesWizard(models.TransientModel):
    _name = 'attribute.variant.values.wizard'
    _description = 'Attribute Variant Values'

    variant_value_ids = fields.Many2many('product.attribute.value', 'product_attribute_value_rel', 'attribute_variant_value_id', 'values_id',
                                         domain="[('id', 'in', allowed_attribute_type_ids)]", string='Variant values')
    product_id = fields.Many2one('product.template', string='Product')
    attribute_family_id = fields.Many2one('family.attribute', string='Families')
    variant_id = fields.Many2one('family.variant.line', string='Variant')
    attribute_id = fields.Many2one('product.attribute', string='Attributes')

    allowed_attribute_type_ids = fields.Many2many(
        'product.attribute.value',
        string='Allowed Attribute Types',
        compute='_compute_allowed_attribute_type_ids',
        store=False
    )

    @api.depends('attribute_family_id')
    def _compute_allowed_attribute_type_ids(self):
        for record in self:
            if record.attribute_family_id:
                # Get the variant line IDs associated with the attribute family
                variant_line_ids = record.attribute_family_id.variant_line_ids
                print(variant_line_ids, 'variant_line_ids')
                # Get the variant IDs from the variant lines
                variant_ids = variant_line_ids.mapped('variant_ids')
                print(variant_ids, 'variant_ids')
                # Get the attribute type IDs from the variants
                attribute_type_ids = variant_ids.mapped('value_ids')
                print(attribute_type_ids, 'attribute_type_ids')
                # Set the allowed attribute type IDs
                record.allowed_attribute_type_ids = attribute_type_ids
            else:
                record.allowed_attribute_type_ids = False

    def update_variant_value_rec(self):
        for rec in self:
            rec.product_id.is_variant_update = True
            product_tmpl = rec.product_id
            product_variants = rec.product_id.product_variant_ids
            rec.product_id.write({
                'product_attr_values_id': [(4, variant.id) for variant in self.variant_value_ids],
            })
            for variant_value in rec.variant_value_ids:
                attribute_line = self.env['product.template.attribute.line'].search([
                    ('product_tmpl_id', '=', product_tmpl.id),
                    ('attribute_id', '=', variant_value.attribute_id.id)
                ], limit=1)

                if not attribute_line:
                    attribute_line = self.env['product.template.attribute.line'].create({
                        'product_tmpl_id': product_tmpl.id,
                        'attribute_id': variant_value.attribute_id.id,
                        'value_ids': [(4, variant_value.id)]
                    })
                else:
                    attribute_line.write({'value_ids': [(4, variant_value.id)]})

            template_attr_values = self.env['product.template.attribute.value'].search([
                ('product_tmpl_id', '=', product_tmpl.id),
                ('product_attribute_value_id', 'in', rec.variant_value_ids.ids)
            ])

            if not template_attr_values:
                raise ValidationError("No matching product.template.attribute.value found for the selected attributes.")

            for variant in product_variants:
                variant.write({
                    'product_template_attribute_value_ids': [(4, ptav.id) for ptav in template_attr_values]
                })

            for combination in product_tmpl._get_possible_combinations():
                product_tmpl._create_product_variant(combination)







