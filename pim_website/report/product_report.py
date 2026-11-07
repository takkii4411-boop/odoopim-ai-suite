from odoo import api, models
from odoo.tools.mail import html2plaintext


class PimProductReport(models.AbstractModel):
    _name = 'report.pim_website.pim_product_report'
    _description = 'PIM Product PDF Report'

    def _clean_html(self, value):
        return html2plaintext(value or '').strip()

    def _get_image_gallery(self, product):
        """
        Returns:
        {
            'primary': base64_string | False,
            'additional': [base64_string, ...]
        }
        """
        image_gallery = {
            'primary': False,
            'additional': [],
        }

        images = product.image_ids.filtered(lambda i: i.image_1920)

        # Primary image first
        primary_img = images.filtered(lambda i: i.is_primary)[:1]

        if primary_img:
            image_gallery['primary'] = primary_img.image_1920.decode('utf-8')

            for img in images.filtered(lambda i: i.id != primary_img.id).sorted('sequence'):
                image_gallery['additional'].append(
                    img.image_1920.decode('utf-8')
                )

        else:
            # no primary → first image is primary
            images = images.sorted('sequence')
            if images:
                image_gallery['primary'] = images[0].image_1920.decode('utf-8')

                for img in images[1:]:
                    image_gallery['additional'].append(
                        img.image_1920.decode('utf-8')
                    )

        # Final fallback → product.image_1920
        if not image_gallery['primary'] and product.image_1920:
            image_gallery['primary'] = product.image_1920.decode('utf-8')

        return image_gallery



    @api.model
    def _get_report_values(self, docids, data=None):
        products = self.env['product.template'].browse(docids)
        website = self.env['website'].get_current_website()

        # Fetch all dynamic attributes that are active and belong to the current company
        all_dynamic_attributes = self.env['product.attribute'].sudo().search([
            ('original_name', '!=', False),
            ('active', '=', True),
            ('company_id', 'in', (False, website.company_id.id))
        ], order='sequence, name')

        product_template_fields = self.env['product.template']._fields
        dynamic_fields_map = {}

        for attr in all_dynamic_attributes:
            field_name = attr.original_name
            if field_name in product_template_fields:
                dynamic_fields_map[attr.name] = {
                    'field_name': field_name,
                    'display_type': attr.display_type,
                    'field_type': product_template_fields[field_name].type,
                }

        product_data = []

        for product in products:
            grouped_data = []

            for grp in product.get_grouped_dynamic_fields():
                filtered_attrs = []

                for att in grp['attributes']:
                    label = att.get('label')
                    field_info = dynamic_fields_map.get(label)
                    if not field_info:
                        continue

                    field_name = field_info['field_name']
                    field_type = field_info['field_type']
                    value = getattr(product, field_name, None)

                    # Normalize values based on field type
                    if field_type == 'many2one':
                        value = value.name if value else False
                    elif field_type == 'many2many':
                        value = value.mapped('name') if value else []
                    elif field_type in ('float', 'integer'):
                        value = value if value not in (0, 0.0) else False

                    # Handle price fields specially
                    if field_info['display_type'] == 'price' and value:
                        value = float(value)

                    # Final filter to remove empty or irrelevant values
                    if value in (None, '', False, [], 0, 0.0):
                        continue

                    filtered_attrs.append({
                        'label': label,
                        'value': value,
                        'field_info': field_info,
                    })

                # Append group only if it has visible attributes
                if filtered_attrs:
                    grouped_data.append({
                        'group': grp['group'],
                        'attributes': filtered_attrs,
                    })

            product_data.append({
                'product': product,
                'images': self._get_image_gallery(product),
                'grouped_fields': grouped_data,
            })

        currency = self.env.company.currency_id

        return {
            'doc_ids': docids,
            'doc_model': 'product.template',
            'docs': product_data,
            'clean_html': self._clean_html,
            'currency': currency,
        }


