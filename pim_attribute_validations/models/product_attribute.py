from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import json
import logging

_logger = logging.getLogger(__name__)


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    max_characters = fields.Integer('Max Characters', default=0)
    regex_pattern = fields.Char('Regular Expression Pattern')
    unique_value = fields.Boolean('Unique Value Required', default=False)

    min_value = fields.Float('Minimum Value', default=0)
    max_value_field = fields.Float('Maximum Value', default=0)
    allow_negative = fields.Boolean('Allow Negative Values', default=True)
    allow_decimals = fields.Boolean('Allow Decimals', default=True)
    decimal_places = fields.Integer('Decimal Places', default=2)

    min_date = fields.Date('Minimum Date')
    max_date = fields.Date('Maximum Date')

    allowed_extensions = fields.Many2many(
        'image.attribute.type',
        'product_attribute_extension_rel',
        'attribute_id',
        'extension_id',
        string='Allowed Extensions',
        help="Select allowed file types"
    )

    max_file_size_mb = fields.Float('Max File Size (MB)', default=5.0)

    metric_family = fields.Selection([
        ('weight', 'Weight'),
        ('length', 'Length'),
        ('volume', 'Volume'),
        ('area', 'Area'),
    ], string='Metric Family')
    default_unit = fields.Many2one('uom.uom', 'Default Unit')

    default_value = fields.Many2one(
        'product.attribute.value',
        domain="[('id', 'in', value_ids)]",
        string="Default Value"
    )

    @api.onchange('allow_decimals')
    def _onchange_allow_decimals(self):
        """Reset decimal_places when decimals not allowed"""
        if not self.allow_decimals:
            self.decimal_places = 0

    @api.onchange('allow_negative')
    def _onchange_allow_negative(self):
        """Reset min_value when allowing negative values"""
        if self.allow_negative:
            self.min_value = 0

    @api.constrains('min_value', 'allow_negative')
    def _check_min_value_negative(self):
        """Ensure min_value is 0 or positive when negative values not allowed"""
        for record in self:
            if not record.allow_negative and record.min_value < 0:
                raise ValidationError(_(
                    'Minimum value cannot be negative when "Allow Negative Values" is disabled.'
                ))

    @api.constrains('allow_decimals', 'decimal_places')
    def _check_decimal_places(self):
        """Ensure decimal_places is valid"""
        for record in self:
            if not record.allow_decimals and record.decimal_places > 0:
                raise ValidationError(_(
                    'Decimal places must be 0 when "Allow Decimals" is disabled.'
                ))
            if record.allow_decimals and record.decimal_places < 0:
                raise ValidationError(_(
                    'Decimal places cannot be negative.'
                ))

    def write(self, vals):
        """Update ir.default when default_value changes"""
        result = super().write(vals)
        print("VALSSS", vals)
        if 'default_value' in vals:
            for record in self:
                record._sync_default_value()

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Set ir.default when attribute is created with default_value"""
        records = super().create(vals_list)

        for record in records:
            if record.default_value and record.product_template_field_id:
                record._sync_default_value()

        return records

    def _sync_default_value(self):
        """Sync default_value to ir.default"""
        self.ensure_one()

        if not self.product_template_field_id:
            _logger.warning(f"No field linked for attribute {self.name}")
            return

        IrDefault = self.env['ir.default'].sudo()

        # Search for existing default
        existing_default = IrDefault.search([
            ('field_id', '=', self.product_template_field_id.id),
            ('user_id', '=', False),
            ('company_id', '=', False),
            ('condition', '=', False)
        ])

        # If no default_value is set, remove existing defaults
        if not self.default_value:
            if existing_default:
                existing_default.unlink()
                _logger.info(
                    f"Removed default value for field {self.product_template_field_id.name}")
            return

        # Only support selection fields
        if self.display_type not in ['simple_select', 'select', 'radio',
                                     'color']:
            if existing_default:
                existing_default.unlink()
            return

        # Get the field type
        field_type = self.product_template_field_id.ttype

        # For Many2one fields (simple_select, select, radio, color)
        if field_type == 'many2one':
            # ir.default expects just the ID for many2one fields
            value = self.default_value.id

            try:
                IrDefault.set(
                    model_name='product.template',
                    field_name=self.product_template_field_id.name,
                    value=value,
                    user_id=False,
                    company_id=False,
                    condition=False
                )
                _logger.info(
                    f"✅ Set default value for {self.product_template_field_id.name}: {value}")
            except Exception as e:
                _logger.error(f"❌ Failed to set default value: {e}")

        # For Many2many fields (multi_select, multi, pills) - if you add support later
        elif field_type == 'many2many':
            # ir.default expects a list of IDs for many2many fields
            value = [self.default_value.id]

            try:
                IrDefault.set(
                    model_name='product.template',
                    field_name=self.product_template_field_id.name,
                    value=value,
                    user_id=False,
                    company_id=False,
                    condition=False
                )
                _logger.info(
                    f"✅ Set default value for {self.product_template_field_id.name}: {value}")
            except Exception as e:
                _logger.error(f"❌ Failed to set default value: {e}")
        else:
            _logger.warning(
                f"Unsupported field type {field_type} for default value")
            if existing_default:
                existing_default.unlink()

    def unlink(self):
        """Remove ir.default when attribute is deleted"""
        IrDefault = self.env['ir.default'].sudo()

        for record in self:
            if record.product_template_field_id:
                defaults = IrDefault.search([
                    ('field_id', '=', record.product_template_field_id.id),
                ])
                defaults.unlink()
                _logger.info(
                    f"Removed defaults for field {record.product_template_field_id.name}")

        return super().unlink()

    def get_validation_rules_json(self):
        """
        Build validation rules as JSON based on display_type
        Returns: dict with validation rules
        """
        self.ensure_one()

        rules = {
            'field_name': self.original_name,
            'attribute_id': self.id,
            'display_type': self.display_type,
            'label': self.name,
            'required': self.is_mandatory,
            'validations': []
        }

        # ============================================================
        # TEXT / TEXTAREA / IDENTIFIER
        # ============================================================
        if self.display_type in ['text', 'textarea', 'identifier']:
            if self.is_mandatory:
                rules['validations'].append({
                    'type': 'required',
                    'value': True,
                    'message': f'{self.name} is required'
                })

            if self.max_characters > 0:
                rules['validations'].append({
                    'type': 'max_characters',
                    'value': self.max_characters,
                    'message': f'Maximum {self.max_characters} characters allowed'
                })

            if self.regex_pattern:
                rules['validations'].append({
                    'type': 'regex_pattern',
                    'value': self.regex_pattern,
                    'message': 'Value does not match required format'
                })

            if self.unique_value:
                rules['validations'].append({
                    'type': 'unique',
                    'value': True,
                    'message': 'Value must be unique'
                })

        # ============================================================
        # NUMBER / FLOAT / PRICE / MEASUREMENT
        # ============================================================
        elif self.display_type in ['number', 'float', 'price', 'measurement']:
            if self.is_mandatory:
                rules['validations'].append({
                    'type': 'required',
                    'value': True,
                    'message': f'{self.name} is required'
                })

            # Negative value validation
            if not self.allow_negative:
                rules['validations'].append({
                    'type': 'no_negative',
                    'value': False,
                    'message': f'{self.name} cannot be negative'
                })

                if self.min_value < 0:
                    min_val = 0
                else:
                    min_val = self.min_value
            else:
                min_val = self.min_value

            # Min value
            if min_val != 0:
                rules['validations'].append({
                    'type': 'min_value',
                    'value': min_val,
                    'message': f'Minimum value is {min_val}'
                })

            # Max value
            if self.max_value_field != 0:
                rules['validations'].append({
                    'type': 'max_value',
                    'value': self.max_value_field,
                    'message': f'Maximum value is {self.max_value_field}'
                })

            # Range
            if min_val != 0 and self.max_value_field != 0:
                rules['validations'].append({
                    'type': 'range',
                    'min': min_val,
                    'max': self.max_value_field,
                    'message': f'Value must be between {min_val} and {self.max_value_field}'
                })

            # Decimal validation
            if not self.allow_decimals:
                rules['validations'].append({
                    'type': 'integer_only',
                    'value': True,
                    'message': f'{self.name} must be a whole number (no decimals allowed)'
                })
            elif self.decimal_places > 0:
                rules['validations'].append({
                    'type': 'max_decimal_places',
                    'value': self.decimal_places,
                    'message': f'Maximum {self.decimal_places} decimal places allowed'
                })

            # Unique value
            if self.unique_value:
                rules['validations'].append({
                    'type': 'unique',
                    'value': True,
                    'message': 'Value must be unique'
                })

        # ============================================================
        # DATE
        # ============================================================
        elif self.display_type == 'date':
            if self.is_mandatory:
                rules['validations'].append({
                    'type': 'required',
                    'value': True,
                    'message': f'{self.name} is required'
                })

            if self.min_date:
                rules['validations'].append({
                    'type': 'min_date',
                    'value': self.min_date.isoformat(),
                    'message': f'Date must be after {self.min_date}'
                })

            if self.max_date:
                rules['validations'].append({
                    'type': 'max_date',
                    'value': self.max_date.isoformat(),
                    'message': f'Date must be before {self.max_date}'
                })

            if self.min_date and self.max_date:
                rules['validations'].append({
                    'type': 'date_range',
                    'min': self.min_date.isoformat(),
                    'max': self.max_date.isoformat(),
                    'message': f'Date must be between {self.min_date} and {self.max_date}'
                })

        # ============================================================
        # FILE / IMAGE - FIXED HERE
        # ============================================================
        elif self.display_type in ['file', 'image']:
            if self.is_mandatory:
                rules['validations'].append({
                    'type': 'required',
                    'value': True,
                    'message': f'{self.name} is required'
                })

            # FIXED: Handle Many2many field properly
            if self.allowed_extensions:
                # Get extensions from Many2many records
                extensions = [ext.extension for ext in self.allowed_extensions]
                extension_names = [ext.name for ext in self.allowed_extensions]

                rules['validations'].append({
                    'type': 'file_extension',
                    'value': extensions,
                    # List of extensions like ['jpg', 'png', 'pdf']
                    'message': f'Allowed file types: {", ".join(extension_names)}'
                })

            if self.max_file_size_mb:
                rules['validations'].append({
                    'type': 'file_size',
                    'value': self.max_file_size_mb,
                    'message': f'Maximum file size: {self.max_file_size_mb} MB'
                })

        # ============================================================
        # SIMPLE_SELECT / MULTI_SELECT / COLOR / SELECT / PILLS / RADIO / MULTI
        # ============================================================
        elif self.display_type in ['simple_select', 'multi_select', 'color',
                                   'select', 'pills', 'radio', 'multi']:
            if self.is_mandatory:
                rules['validations'].append({
                    'type': 'required',
                    'value': True,
                    'message': f'{self.name} is required'
                })

            if self.default_value:
                rules['validations'].append({
                    'type': 'default_value',
                    'value': {
                        'id': self.default_value.id,
                        'name': self.default_value.name
                    },
                    'message': f'Default value: {self.default_value.name}'
                })

        # ============================================================
        # YES_NO (BOOLEAN/CHECKBOX)
        # ============================================================
        elif self.display_type == 'yes_no':
            if self.is_mandatory:
                rules['validations'].append({
                    'type': 'required',
                    'value': True,
                    'message': f'{self.name} must be checked'
                })

        return rules

