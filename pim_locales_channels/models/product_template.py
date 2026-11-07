from odoo import models, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def prepare_channel_local_vals(self, field_names=False, channels=False):
        """Before sending new channels you must create the models for them to save the data
        eg: f'x_{channel}_locale_save' this is where the channel goes"""
        if not field_names:
            fields = self.env['ir.model.fields'].sudo().search(
                [('model', '=', self._name),
                 ('name', 'in', list(self._fields.keys())),
                 ('ttype', 'in', self.available_field_types()),
                 '|',
                 ('m_translate', '=', True),
                 ('m_channelization', '=', True)]
            )
            field_names = [x.name for x in fields]
        platforms = self.env['platform.credentials'].sudo().search_read(
            domain=[('is_active', '=', True)],
            fields=['id', 'platform']
        )
        channels = [x['platform'] for x in platforms]
        return super(ProductTemplate, self).prepare_channel_local_vals(field_names, channels)

    def get_read_channel(self):
        super().get_read_channel()
        return self.env.user.m_channel_id.platform

    def check_system_ready(self):
        if not self.env.user.m_channel_id:
            raise ValidationError("User Channel can not find")
        if not self.env["platform.credentials"].search([('is_active', '=', True)]):
            raise ValidationError("No platforms found please create one.")
        super(ProductTemplate, self).check_system_ready()
