from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pim_workflow_id = fields.Many2one('pim.workflow', string='Assigned Workflow', readonly=True)
