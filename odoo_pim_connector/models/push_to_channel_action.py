from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_push_to_channel_n8n(self):
        return {
            'name': 'Publish to Channel',
            'type': 'ir.actions.act_window',
            'res_model': 'push.to.channel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_ids': [(6, 0, self.ids)],
            }
        }
