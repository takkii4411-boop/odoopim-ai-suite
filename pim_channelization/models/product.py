from odoo import models, api
from lxml import etree

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super(ProductTemplate, self).get_view(view_id, view_type, **options)
        pim_channel = self.env.user.m_channel_id
        if pim_channel and view_type == 'form' and result.get('arch'):
            arch_tree = etree.fromstring(result['arch'])

            def find_field_nodes(node, field_name):
                nodes = []
                if node.tag == 'field' and node.get('name') == field_name:
                    nodes.append(node)
                for child in node:
                    nodes.extend(find_field_nodes(child, field_name))
                return nodes

            # Get all fields for this model that need channelisation
            channel_attributes = self.env['product.attribute'].sudo().search(
                [('company_id', '=', self.env.company.id),
                 ('is_value_per_channel', '=', True),
                 ('platform_credential_ids','!=', False)])
            
            if not channel_attributes:
                result['arch'] = etree.tostring(arch_tree, encoding='unicode')
                return result

            for attr in channel_attributes:
                field_name = attr.original_name
                channel = [x for x in attr.platform_credential_ids if x.platform == pim_channel.platform]
                for rec in channel:
                    logo_url = f"{self.get_base_url()}/web/image/platform.credentials/{rec.id}/logo_image"
                    for field_node in find_field_nodes(arch_tree, field_name):
                        parent = field_node.getparent()
                        if parent is not None:
                            br = etree.Element('br')
                            parent.insert(parent.index(field_node), br)

                            # 2. Create badge: logo + channel name
                            badge = etree.Element('div')
                            badge.set('class', 'o_badge_channel rounded-pill d-flex align-items-center')
                            badge.set('style', '''
                                                float: right;
                                                background: #f8f9fa;
                                                border: 1px solid #dee2e6;
                                                border-radius: 4px;
                                                padding: 3px 7px;
                                                font-size: 7px;
                                                font-weight: bold;
                                                color: #333;
                                                gap: 6px;
                                                margin-top: -4px;
                                            ''')

                            # Logo on the left
                            if logo_url:
                                img = etree.Element('img')
                                img.set('src', logo_url)
                                img.set('alt', pim_channel.platform)
                                img.set('style', 'height: 16px; width: auto;')
                                badge.append(img)

                            # Channel name
                            span = etree.Element('span')
                            span.text = pim_channel.platform.upper()
                            badge.append(span)
                            parent.insert(parent.index(field_node) , badge)
            # Update the arch

            result['arch'] = etree.tostring(arch_tree, pretty_print=True).decode()
        return result



class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super(ProductProduct, self).get_view(view_id, view_type, **options)
        pim_channel = self.env.user.m_channel_id
        if pim_channel and view_type == 'form' and result.get('arch'):
            arch_tree = etree.fromstring(result['arch'])

            def find_field_nodes(node, field_name):
                nodes = []
                if node.tag == 'field' and node.get('name') == field_name:
                    nodes.append(node)
                for child in node:
                    nodes.extend(find_field_nodes(child, field_name))
                return nodes

            # Get all fields for this model that need channelisation
            channel_attributes = self.env['product.attribute'].sudo().search(
                [('company_id', '=', self.env.company.id),
                 ('is_value_per_channel', '=', True), ('platform_credential_ids', '!=', False)])

            if not channel_attributes:
                result['arch'] = etree.tostring(arch_tree, encoding='unicode')
                return result

            for attr in channel_attributes:
                field_name = attr.original_name
                channel = [x for x in attr.platform_credential_ids if x.platform == pim_channel.platform]
                for rec in channel:
                    logo_url = f"{self.get_base_url()}/web/image/platform.credentials/{rec.id}/logo_image"
                    for field_node in find_field_nodes(arch_tree, field_name):
                        parent = field_node.getparent()
                        if parent is not None:
                            br = etree.Element('br')
                            parent.insert(parent.index(field_node), br)

                            # 2. Create badge: logo + channel name
                            badge = etree.Element('div')
                            badge.set('class', 'o_badge_channel rounded-pill d-flex align-items-center')
                            badge.set('style', '''
                                                    float: right;
                                                    background: #f8f9fa;
                                                    border: 1px solid #dee2e6;
                                                    border-radius: 4px;
                                                    padding: 3px 7px;
                                                    font-size: 7px;
                                                    font-weight: bold;
                                                    color: #333;
                                                    gap: 6px;
                                                    margin-top: -4px;
                                                ''')

                            # Logo on the left
                            if logo_url:
                                img = etree.Element('img')
                                img.set('src', logo_url)
                                img.set('alt', pim_channel.platform)
                                img.set('style', 'height: 14px; width: auto;')
                                badge.append(img)

                            # Channel name
                            span = etree.Element('span')
                            span.text = pim_channel.platform.upper()
                            badge.append(span)
                            parent.insert(parent.index(field_node) , badge)
            # Update the arch

            result['arch'] = etree.tostring(arch_tree, pretty_print=True).decode()
        return result
