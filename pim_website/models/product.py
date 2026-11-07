from odoo import models
from odoo.http import request
from odoo.tools.mail import html2plaintext

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_grouped_dynamic_attributes(self):
        """
        Returns:
        [
            {
                'group_name': str,
                'group_description': str,
                'attributes': [
                    {'label': str, 'value': str}
                ]
            }
        ]
        """
        self.ensure_one()
        result = []

        # All attribute groups (company-safe)
        groups = self.env['attribute.group'].search([
            ('active', '=', True),
            ('company_id', '=', self.company_id.id)
        ])

        for group in groups:
            attrs_data = []

            for attribute in group.attributes_ids:
                field_name = attribute.name  # assuming attribute.name == dynamic field name

                if field_name in self._fields:
                    value = self[field_name]

                    if value:
                        # format value safely
                        if hasattr(value, 'name'):
                            value = value.name
                        elif isinstance(value, models.BaseModel):
                            value = ', '.join(value.mapped('name'))

                        attrs_data.append({
                            'label': attribute.display_name,
                            'value': value
                        })

            if attrs_data:
                result.append({
                    'group_name': group.name,
                    'group_description': group.description or '',
                    'attributes': attrs_data
                })

        return result

    def _clean_html(self, value):
        return html2plaintext(value or "").strip()

    def get_grouped_dynamic_fields(self):
        website = request.env['website'].get_current_website()
        company = website.company_id

        product_fields = self._fields
        rendered = set()
        result = []

        groups = request.env['attribute.group'].sudo().search([
            ('active', '=', True),
            ('company_id', '=', company.id),
        ], order='id')

        for group in groups:
            if group.name.lower() in ('default', 'general'):
                continue

            attrs = []
            for line in group.attribute_group_line_ids.filtered('enable'):
                attr = line.product_attribute_id
                if not attr or attr.id in rendered:
                    continue

                field_name = attr.original_name
                if field_name not in product_fields:
                    continue

                value = getattr(self, field_name)
                if product_fields[field_name].type == 'many2one':
                    value = value.name if value else ''
                elif product_fields[field_name].type == 'many2many':
                    value = ', '.join(value.mapped('name'))
                else:
                    value = self._clean_html(str(value))

                if value:
                    attrs.append({
                        'label': attr.name,
                        'value': value,
                    })
                    rendered.add(attr.id)

            if attrs:
                result.append({
                    'group': group.name,
                    'attributes': attrs,
                })

        return result
