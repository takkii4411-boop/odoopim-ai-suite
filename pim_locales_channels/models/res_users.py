from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_default_m_lang(self):
        """Set default Language for pim product localization"""
        lang = self.env['res.lang'].search([('code', '=', 'en_US')], limit=1)
        return lang.id if lang else False

    def _get_default_m_channel(self):
        """set default channel for pim product Channelization"""
        channel = self.env['platform.credentials'].search([('is_active', '=', True)], limit=1)
        return channel.id if channel else False

    m_lang_id = fields.Many2one("res.lang",
                                string="PIM Language",
                                default=_get_default_m_lang)
    m_channel_id = fields.Many2one("platform.credentials",
                                   string="PIM Channel",
                                   default=_get_default_m_channel)

    @api.model
    def get_channel_and_translation(self):
        """Get the default Channel and language"""
        user = self or self.env.user
        return {
            'active_lang_id': user.m_lang_id.id or False,
            'active_channel_id': user.m_channel_id.id or False,
            'active_channel': user.m_channel_id.platform or "",
            'active_lang': user.m_lang_id.code or "",
            'allowed_lang_ids': self.env.company.pim_available_lang_ids.ids or []
        }
