from odoo import models, fields, api


class GeneralAttributes(models.Model):
    _name = 'general.attribute'
    _description ="General Attribute"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Attribute Name")
    related_field = fields.Many2one('ir.model.fields', ondelete="cascade")
    model = fields.Char(string='Model',related='related_field.model_id.name')
    completeness = fields.Boolean(string="Completeness?")
    is_ai_enrichable = fields.Boolean(
        string="AI Enrichable",
        store=True,
    )

    original_name = fields.Char('Field Names')
