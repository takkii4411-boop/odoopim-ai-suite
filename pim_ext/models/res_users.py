from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    product_lang = fields.Char("Product Main Lang",
                               default=lambda self: self.env.context.get('lang') or self.env.user.lang)

