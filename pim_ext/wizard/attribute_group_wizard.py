# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AttributeGroupWizard(models.TransientModel):
    _name = 'attribute.group.wizard'
    _description = 'Attribute Group Wizard'

    attribute_group_ids = fields.Many2many('attribute.group', string='Attribute Groups', required=True)
    attribute_family_id = fields.Many2one('family.attribute', string='Families')
    exist_group_ids = fields.Many2many('attribute.group', related='attribute_family_id.exist_group_ids')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def apply_group_attributes(self):
        # Get the 'family.attribute' record using the family_id
        family = self.attribute_family_id

        # Create a dictionary to store the attributes grouped by attribute_group_id
        grouped_attributes = {}

        # Loop through each group and its attributes
        for group in self.attribute_group_ids:
            for attribute in group.attribute_group_line_ids:

                # Prepare the record to be added to the grouped_attributes
                attribute_data = {
                    'attribute_id': attribute.product_attribute_id.id,
                    'attribute_group_id': group.id,
                }

                # Group attributes by attribute_group_id
                if group.id not in grouped_attributes:
                    grouped_attributes[group.id] = []
                grouped_attributes[group.id].append(attribute_data)

        # Now create the records for product_families_ids based on the grouped data
        values_to_write = []
        print("attribute_data === ", grouped_attributes)
        for group_id, attributes in grouped_attributes.items():
            for attribute_data in attributes:
                values_to_write.append((0, 0, attribute_data))

        # Write the grouped attributes into product_families_ids
        if values_to_write:
            family.write({
                'family_attribute_ids': values_to_write,
            })
