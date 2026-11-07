from odoo import models, api


class PlatformCredentials(models.Model):
    _inherit = 'platform.credentials'

    @api.model
    def get_all_active_channels(self):
        """To retrieve all values from platform credentials with field mapping"""
        channels = self.env['platform.credentials'].sudo().search([('is_active', '=', True)])
        return [{'id': x.id, 'name': x.name, 'platform': x.platform, 'field_map_ids': x.get_field_mappings()} for x in
                channels]

    def get_field_mappings(self):
        """retrieve all the field mapping of current connector"""
        field_mapping_id = self.env['pim.platform.mapping'].sudo().search([('platform_id', '=', self.id)], limit=1)
        return [{'odoo_name': x.odoo_field_id.name, 'ext_name': x.external_field_key} for x in
                field_mapping_id.mapping_line_ids] if field_mapping_id else []
