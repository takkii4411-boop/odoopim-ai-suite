from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    is_channel_locale = fields.Boolean()
    pim_available_lang_ids = fields.Many2many("res.lang")
    lc_available_model_ids = fields.Many2many("ir.model")

    def get_langs_and_channels(self):
        """Return languages and active channels in one DB round-trip.
        This method is called very often from JS"""
        user = self.env.user
        company = self
        channels = self.env['platform.credentials'].sudo().search_read(
            domain=[('is_active', '=', True)],
            fields=['id', 'platform'],
            order='platform'
        )
        channels = [{'id': c['id'], 'name': c['platform']} for c in channels]
        langs = [
            {'id': lang.id, 'name': lang.name, 'code': lang.code}
            for lang in company.pim_available_lang_ids
        ]
        return {
            'channels': channels,
            'langs': langs,
            'is_channel_locale': company.is_channel_locale,
            'active_channel': user.m_channel_id.id,
            'active_lang': user.m_lang_id.id,
        }
