from odoo import models, fields

class N8NWorkflowConfig(models.Model):
    _name = "n8n.workflow.config"
    _description = "N8N Workflow Configuration"

    name = fields.Char("Workflow Name", required=True)
    platform = fields.Selection([
        ("shopware", "Shopware"),
        ("magento", "Magento 2"),
        ("sellercloud", "Sellercloud"),
        ("shopify", "Shopify"),
        ("amazon", "Amazon"),
        ("flipkart", "Flipkart"),
        ("ebay", "eBay"),
        ("walmart", "Walmart"),
    ], required=True)

    n8n_workflow_id = fields.Char("Workflow ID", required=True)
    n8n_webhook_url = fields.Char("Webhook URL", required=True)

    is_active = fields.Boolean("Active", default=True)
