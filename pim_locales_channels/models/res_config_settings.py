from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_channel_locale = fields.Boolean(string="Enable Channels And Locale",
                                           related='company_id.is_channel_locale',
                                           readonly=False)
    pim_available_lang_ids = fields.Many2many("res.lang", string="Available Languages",
                                              help="Select languages to translate in PIM",
                                              related='company_id.pim_available_lang_ids',
                                              readonly=False)
    lc_available_model_ids = fields.Many2many("ir.model",
                                              readonly=False,
                                              related='company_id.lc_available_model_ids')