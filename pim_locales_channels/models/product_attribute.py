from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    platform_credential_ids = fields.Many2many("platform.credentials")

    def prepare_attribute_field_vals(self, model):
        """Prepare attribute field values and mark for translation in
        view if `value_per_locale` is enabled."""
        base_val, sub_val = super().prepare_attribute_field_vals(model)
        if self.is_value_per_channel:
            base_val['m_channelization'] = True
        if self.is_value_per_locale:
            base_val['m_translate'] = True
        return base_val, sub_val

    def update_product_channel_fields(self):
        """Update field values"""
        if self.product_product_field_id:
            self.product_product_field_id.write({
                'm_channelization': self.is_value_per_channel,
                'm_translate': self.is_value_per_locale
            })
        if self.product_template_field_id:
            self.product_template_field_id.write({
                'm_channelization': self.is_value_per_channel,
                'm_translate': self.is_value_per_locale
            })

    def write(self, vals):
        res = super(ProductAttribute, self).write(vals)
        for rec in self:
            rec.update_product_channel_fields()
        return res
