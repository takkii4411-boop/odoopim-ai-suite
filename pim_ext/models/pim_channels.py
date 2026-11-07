# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PIMChannel(models.Model):
    _name = 'pim.channel'
    _description = 'Channels'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Channel Name', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    locale_id = fields.Many2one('res.lang', string='Locale', required=True)
    category_id = fields.Many2one('pim.category', string='Category Tree', required=True)

    def create_pim_channels(self):
        return {
            'name': _('Create Channel'),
            'res_model': 'pim.channel',
            'view_mode': 'form',
            'type': 'ir.actions.act_window'
        }
