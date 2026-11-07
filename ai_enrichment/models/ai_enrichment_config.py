from odoo import api, fields, models

class AIEnrichmentConfig(models.Model):
    _name = 'ai.enrichment.config'
    _description = 'AI Enrichment Configuration'
    _order = 'sequence, name'
    # By not defining _rec_name, we force Odoo to use the name_get() method below.

    name = fields.Char(string='Model Name', required=True, help="A user-friendly name for this configuration, e.g., 'Groq Llama 3'")
    code = fields.Char(string='Model Code', required=True, index=True, help="The specific model identifier for API calls, e.g., 'llama3-70b-8192'")
    sequence = fields.Integer(default=10)

    provider = fields.Selection([
        ('google', 'Google'),
        ('openai', 'OpenAI'),
        ('groq', 'Groq'),
        ('claude', 'Claude'),
    ], string='AI Provider', required=True, index=True)

    api_key = fields.Char(string="API Key",required=True)
    api_token = fields.Char(string="API Token")
    api_url = fields.Char(string="API URL",required=True)

    _sql_constraints = [
        ('code_provider_uniq', 'unique(code, provider)', 'Model code must be unique per provider.'),
    ]

    user_name = fields.Char()
    password = fields.Char()
    manual_credentials = fields.Boolean()
    # This method defines the text that will appear in dropdowns.
    def name_get(self):
        # Create a dictionary to map the selection key to its label
        # e.g., {'google': 'Google', 'groq': 'Groq'}
        provider_labels = dict(self._fields['provider'].selection)

        result = []
        for rec in self:
            # Get the label for the current record's provider key
            provider_name = provider_labels.get(rec.provider, rec.provider)
            # We will format it as "Provider (Model Name)" for clarity
            display_name = f"{provider_name} ({rec.name})"
            result.append((rec.id, display_name))
        return result

    @api.model
    def get_ai_provider_count(self):
        """Return count of unique AI providers"""
        providers = self.search_read([], ['provider'])
        unique_providers = set(provider['provider'] for provider in providers)
        return len(unique_providers)

# For Sync Configurations
class TriggerSyncConfig(models.Model):
    _name = 'trigger.sync.config'
    _description = 'AI Sync Configuration'

    trigger_api_key = fields.Char(string="Sync API Key", default='tr_prod_7ePqzXb9sWosq2amdx4D', help="API Key for Sync service.")
    trigger_api_url = fields.Char(string="Sync API URL", default='https://api.trigger.dev/api/v1/tasks/product-enrichment/trigger', help="API URL for Sync service.")
    trigger_task_identifier = fields.Char(string="Sync Task Identifier", default='product-enrichment', help="Task Identifier for Sync service.")
