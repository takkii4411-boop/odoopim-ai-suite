from odoo import models, fields, api


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    m_translate = fields.Boolean()
    m_channelization = fields.Boolean()