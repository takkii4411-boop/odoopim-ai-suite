from odoo import models, fields, api

# Define the static destination fields for Shopware
SHOPWARE_FIELDS = [
    ('name', 'Name'),
    ('productNumber', 'Product Number (SKU)'),
    ('stock', 'Stock'),
    ('price', 'Price'),
    ('active', 'Active'),
    ('image', 'Image' ),
]

class PimFieldMapping(models.Model):
    _name = 'pim.field.mapping'
    _description = 'PIM Field Mapping'
    _order = 'platform_id, sequence'

    sequence = fields.Integer(default=10)
    
    platform_id = fields.Many2one(
        'platform.credentials', string="Connector", required=True,
        domain="[('is_coming_soon', '=', False)]"
    )
    
    # ADD ondelete='cascade' TO THIS FIELD
    odoo_model_id = fields.Many2one(
        'ir.model', string="Odoo Model", required=True,
        default=lambda self: self.env.ref('product.model_product_template').id,
        ondelete='cascade'
    )
    
    odoo_field_id = fields.Many2one(
        'ir.model.fields', string="Odoo Source Field", required=True,
        domain="[('model_id', '=', odoo_model_id), ('store', '=', True)]",
        ondelete='cascade'
    )
    
    external_field_key = fields.Selection(
        selection=SHOPWARE_FIELDS, 
        string="Shopware Destination Field", 
        required=True
    )
    
    is_required = fields.Boolean(string="Is Mandatory?", default=False, readonly=True,
                                help="Mandatory mappings are created automatically and cannot be deleted.")

    _sql_constraints = [
        ('unique_mapping', 'unique(platform_id, external_field_key)', 
         'A mapping for this destination field already exists for this platform!')
    ]
