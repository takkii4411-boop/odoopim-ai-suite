from odoo import models, fields

class ComingSoonWizard(models.TransientModel):
    _name = 'coming.soon.wizard'
    _description = 'Coming Soon Wizard'

    message = fields.Text(
        string="Information",
        readonly=True,
        default="This connector is currently under development and will be available in a future update. Thank you for your interest!"
    )