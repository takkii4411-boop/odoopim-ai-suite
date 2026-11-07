from odoo import fields, models

class AIEnrichmentFailureLine(models.Model):
    _name = 'ai.enrichment.failure.line'
    _description = 'AI Enrichment Generation Failure Line'

    log_id = fields.Many2one(
        'ai.enrichment.queue.log', 
        string="Queue Log", 
        required=True, 
        ondelete='cascade'
    )
    product_sku = fields.Char(string="Product SKU")
    product_name = fields.Char(string="Product Name")
    error_details = fields.Char(string="Error Details")