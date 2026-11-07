from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_push_to_channel_n8n(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Publish to Channel',
            'res_model': 'push.to.channel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_ids': [(6, 0, self.ids)],
            }
        }

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_push_to_channel_n8n(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Publish to Channel',
            'res_model': 'push.to.channel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_variant_ids': [(6, 0, self.ids)],
            }
        }
