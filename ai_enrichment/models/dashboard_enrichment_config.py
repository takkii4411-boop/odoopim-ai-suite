from odoo import models, fields

class PromptType(models.Model):
    _name = "ai.prompt.type"
    _description = "Prompt Type"


    name = fields.Selection([
        ('Shorten', 'Shorten'), ('Elaborate', 'Elaborate'), ('Formalize', 'Formalize'),
        ('Polish', 'Polish'), ('Simplify', 'Simplify'), ('Summarize', 'Summarize'),
        ('Rephrase', 'Rephrase'), ('Creative', 'Creative'), ('Technical', 'Technical'),
        ('Marketing', 'Marketing'), ('Short Description', 'Short Description'),
        ('Long Description', 'Long Description'), ('Professional', 'Professional Tone'),
        ('Casual', 'Casual Tone'),
    ], string="Prompt Type", required=True)




class AIDashboardConfig(models.Model):
    _name = 'ai.dashboard.config'
    _description = 'AI Dashboard Configuration'

    name = fields.Char(string='Name')
    # Add fields as needed
