from odoo import models, fields

class IrFilters(models.Model):
    _inherit = 'ir.filters'

    shared_user_ids = fields.Many2many(
        'res.users',
        string="Shared With",
        help="Users who can see and use this filter (in addition to the owner)"
    )

    def action_save_users(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

