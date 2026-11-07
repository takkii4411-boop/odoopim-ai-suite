from odoo import models, fields, api

SHOPWARE_FIELDS = [
    ('name', 'Name'),
    ('productNumber', 'Product Number (SKU)'),
    ('stock', 'Stock'),
    ('price', 'Price'),
    ('active', 'Active'),
]

MAGENTO_FIELDS = [
    ('sku', 'SKU'),
    ('name', 'Name'),
    ('price', 'Price'),
    ('status', 'Status'),
    ('visibility', 'Visibility'),
    ('type_id', 'Product Type'),
    ('weight', 'Weight'),
    ('qty', 'Quantity'),
    ('description', 'Description'),
]

SHOPIFY_FIELDS = [
    ('sku', 'Handle'),
    ('name', 'Title'),
    ('type_id', 'Product Type'),
    ('image', 'Image Src'),
    ('status', 'Status'),
    ('price', 'Price'),
    ('barcode', 'Barcode'),
    ('weight', 'Weight'),
]


class PimPlatformMapping(models.Model):
    _name = 'pim.platform.mapping'
    _description = 'PIM Platform Field Mapping Configuration'

    platform_id = fields.Many2one(
        'platform.credentials', string="Connector", required=True, readonly=True, ondelete='cascade')
    name = fields.Char(related='platform_id.name', readonly=True)
    logo_image = fields.Binary(related='platform_id.logo_image', readonly=True)
    
    mapping_line_ids = fields.One2many(
        'pim.field.mapping.line', 'platform_mapping_id', string="Field Mappings")

    _sql_constraints = [
        ('platform_id_uniq', 'unique(platform_id)', 'A mapping configuration for this platform already exists.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.platform_id.platform == 'shopware':
                rec._create_shopware_default_mappings()
            elif rec.platform_id.platform == 'magento':
                rec._create_magento_default_mappings()
            elif rec.platform_id.platform == 'shopify':
                rec._create_shopify_default_mappings()
        return records

    def _create_shopware_default_mappings(self):
        self.ensure_one()
        MappingLine = self.env['pim.field.mapping.line']
        
        name_field = self.env.ref('product.field_product_template__name')
        sku_field = self.env.ref('product.field_product_template__default_code')
        stock_field = self.env.ref('stock.field_product_template__qty_available')
        price_field = self.env.ref('product.field_product_template__list_price')
        active_field = self.env.ref('product.field_product_template__active')

        default_maps = [
            {'odoo': name_field, 'external': 'name'},
            {'odoo': sku_field, 'external': 'productNumber'},
            {'odoo': stock_field, 'external': 'stock'},
            {'odoo': price_field, 'external': 'price'},
            {'odoo': active_field, 'external': 'active'},
        ]

        for mapping in default_maps:
            MappingLine.create({
                'platform_mapping_id': self.id,
                'odoo_field_id': mapping['odoo'].id,
                'external_field_key': mapping['external'],
                'is_required': True,
            })

    def _create_magento_default_mappings(self):
        self.ensure_one()
        MappingLine = self.env['pim.field.mapping.line']

        sku_field = self.env.ref('product.field_product_template__default_code')
        name_field = self.env.ref('product.field_product_template__name')
        price_field = self.env.ref('product.field_product_template__list_price')
        active_field = self.env.ref('product.field_product_template__active')
        weight_field = self.env.ref('product.field_product_template__weight', raise_if_not_found=False)
        qty_field = self.env.ref('stock.field_product_template__qty_available', raise_if_not_found=False)
        description_field = self.env.ref('product.field_product_template__description', raise_if_not_found=False)

        default_maps = [
            {'odoo': sku_field, 'external': 'sku'},
            {'odoo': name_field, 'external': 'name'},
            {'odoo': price_field, 'external': 'price'},
            {'odoo': active_field, 'external': 'status'},
        ]
        if weight_field:
            default_maps.append({'odoo': weight_field, 'external': 'weight'})
        if qty_field:
            default_maps.append({'odoo': qty_field, 'external': 'qty'})
        if description_field:
            default_maps.append({'odoo': description_field, 'external': 'description'})

        for mapping in default_maps:
            MappingLine.create({
                'platform_mapping_id': self.id,
                'odoo_field_id': mapping['odoo'].id,
                'external_field_key': mapping['external'],
                'is_required': True,
            })

    def _create_shopify_default_mappings(self):
        self.ensure_one()
        MappingLine = self.env['pim.field.mapping.line']

        sku_field = self.env.ref('product.field_product_template__default_code')
        name_field = self.env.ref('product.field_product_template__name')
        type_field = self.env.ref('product.field_product_template__categ_id')
        image_field = self.env.ref('product.field_product_template__image_1920')
        status_field = self.env.ref('product.field_product_template__active')
        price_field = self.env.ref('product.field_product_template__list_price')
        barcode_field = self.env.ref('product.field_product_template__barcode')
        weight_field = self.env.ref('product.field_product_template__weight', raise_if_not_found=False)
        default_maps = [
            {'odoo': sku_field, 'external': 'handle'},
            {'odoo': name_field, 'external': 'title'},
            {'odoo': type_field, 'external': 'product_type'},
            {'odoo': image_field, 'external': 'image'},
            {'odoo': status_field, 'external': 'status'},
            {'odoo': price_field, 'external': 'price'},
            {'odoo': barcode_field, 'external': 'barcode'},
            {'odoo': weight_field, 'external': 'weight'} if weight_field else None,
        ]


        for mapping in default_maps:
            MappingLine.create({
                'platform_mapping_id': self.id,
                'odoo_field_id': mapping['odoo'].id,
                'external_field_key': mapping['external'],
                'is_required': True,
            })

class PimFieldMappingLine(models.Model):
    _name = 'pim.field.mapping.line'
    _description = 'PIM Field Mapping Line'
    _order = 'is_required desc, sequence'

    sequence = fields.Integer(default=10)
    platform_mapping_id = fields.Many2one(
        'pim.platform.mapping', string="Platform Mapping",
        required=True, ondelete='cascade'
    )
    
    odoo_field_id = fields.Many2one(
        'ir.model.fields', string="Odoo Source Field", required=True,
        domain="[('model', '=', 'product.template'), ('store', '=', True)]",
        ondelete='cascade'
    )

    external_field_key = fields.Char(string="External Destination Field", required=True)


    is_required = fields.Boolean(string="Mandatory", default=False, readonly=True)

    def get_platform_fields(self):
        platform = self.platform_mapping_id.platform_id.platform if self.platform_mapping_id else 'shopware'
        print("Platform in get_platform_fields::::::::::::::::::::::::::::::::::::::::", platform)
        if platform == 'magento':
            return MAGENTO_FIELDS
        elif platform == 'shopify':
            return SHOPIFY_FIELDS
        return SHOPWARE_FIELDS
