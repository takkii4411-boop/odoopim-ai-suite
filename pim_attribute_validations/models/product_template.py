from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import logging
import base64
import base64
import math

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'


    def fields_get(self, allfields=None, attributes=None):
        """Override to dynamically set required attribute on dynamic fields"""
        res = super(ProductTemplate, self).fields_get(allfields, attributes)

        company = self.env.company
        sanitize = lambda s: re.sub(
            r'_+', '_',
            re.sub(r'[^a-z0-9_]', '_',
                   s.lower().replace(' #', '_1').replace('-', ''))
        ).strip('_')
        company_suffix = sanitize(company.name or '')

        # Get all mandatory dynamic fields
        mandatory_attrs = self.env['product.attribute'].search([
            ('is_mandatory', '=', True),
            ('company_id', '=', company.id),
            ('active', '=', True)
        ])

        for attr in mandatory_attrs:
            field_name = attr.original_name
            if field_name in res:
                res[field_name]['required'] = True
                res[field_name]['string'] = attr.name + ' *'

        return res

    def validate_dynamic_field(self, field_name, field_value):
        """Validate a single dynamic field in real-time"""
        self.ensure_one()

        company = self.env.company
        sanitize = lambda s: re.sub(
            r'_+', '_',
            re.sub(r'[^a-z0-9_]', '_',
                   s.lower().replace(' #', '_1').replace('-', ''))
        ).strip('_')
        company_suffix = sanitize(company.name or '')

        if not (field_name.startswith('x_') and
                field_name.endswith(f'_{company_suffix}')):
            return {'valid': True, 'error': None}

        attr = self.env['product.attribute'].search([
            ('original_name', '=', field_name),
            ('company_id', '=', company.id),
            ('active', '=', True)
        ], limit=1)

        if not attr:
            return {'valid': True, 'error': None}

        rules = attr.get_validation_rules_json()
        validations = rules.get('validations', [])

        for validation in validations:
            v_type = validation['type']
            v_value = validation.get('value')
            v_message = validation['message']


            # Required check
            if v_type == 'required':
                is_empty = False

                if attr.display_type in ['text', 'textarea', 'identifier',
                                         'char']:
                    is_empty = field_value in [False, None, '']
                elif attr.display_type in ['number', 'float', 'price',
                                           'measurement', 'integer']:
                    is_empty = field_value in [False, None, '']
                elif attr.display_type == 'date':
                    is_empty = field_value in [False, None, '']
                elif attr.display_type in ['simple_select', 'select', 'radio',
                                           'color']:
                    is_empty = field_value in [False, None, '']
                elif attr.display_type in ['multi_select', 'multi', 'pills']:
                    if isinstance(field_value, list):
                        if len(field_value) > 0 and isinstance(field_value[0],
                                                               tuple):
                            is_empty = len(field_value[0]) < 3 or not \
                            field_value[0][2]
                        else:
                            is_empty = len(field_value) == 0
                    else:
                        is_empty = field_value in [False, None, '']
                elif attr.display_type == 'yes_no':
                    is_empty = field_value in [False, None]
                elif attr.display_type in ['file', 'image']:
                    is_empty = field_value in [False, None, '']
                else:
                    is_empty = field_value in [False, None, '', []]

                if is_empty:
                    return {
                        'valid': False,
                        'error': v_message,
                        'field_label': rules['label']
                    }

            if field_value in [False, None, '', []]:
                continue

            # ============= FILE/IMAGE VALIDATIONS =============

            # File extension validation
            if v_type == 'file_extension' and attr.display_type in ['file','image']:
                _logger.info("🔍 [File Validation] Checking file extension...")
                try:
                    if isinstance(field_value, str) and field_value:
                        _logger.info(
                            f"📄 [File Validation] Received base64 string length: {len(field_value)}")

                        # Detect file type from base64 signature (magic bytes)
                        file_extension = self._detect_file_type_from_base64(
                            field_value)

                        if not file_extension:
                            return {
                                'valid': False,
                                'error': 'Unable to detect file type',
                                'field_label': rules['label']
                            }

                        _logger.info(
                            f"🔎 [File Validation] Detected extension: {file_extension}")

                        allowed_extensions = [ext.lower() for ext in v_value]
                        _logger.info(
                            f"✅ [File Validation] Allowed extensions: {allowed_extensions}")

                        if file_extension not in allowed_extensions:
                            allowed_names = ', '.join(
                                [ext.upper() for ext in allowed_extensions])
                            error_msg = f'{v_message} (uploaded: {file_extension.upper()})'

                            _logger.error(
                                f"❌ [File Validation] Extension rejected: {file_extension}")

                            return {
                                'valid': False,
                                'error': error_msg,
                                'field_label': rules['label']
                            }

                        _logger.info(
                            f"✅ [File Validation] Extension valid: {file_extension}")

                except Exception as e:
                    _logger.error(
                        f"💥 [File Validation] Extension check error: {e}",
                        exc_info=True)
                    pass

            # File size validation
            elif v_type == 'file_size' and attr.display_type in ['file', 'image']:
                _logger.info("🔍 [File Validation] Checking file size...")
                try:
                    if isinstance(field_value, str) and field_value:
                        # Remove any whitespace or newlines
                        clean_base64 = field_value.replace('\n', '').replace(
                            '\r', '').replace(' ', '')

                        _logger.info(
                            f"📏 [File Validation] Base64 length: {len(clean_base64)}")

                        # Calculate file size in bytes
                        # Formula: size_in_bytes = (base64_length * 3 / 4) - padding_count
                        base64_length = len(clean_base64)
                        padding_count = clean_base64.count('=')

                        size_in_bytes = (base64_length * 3 / 4) - padding_count
                        size_in_mb = size_in_bytes / (1024 * 1024)

                        max_size_mb = v_value

                        _logger.info(
                            f"📊 [File Validation] File size: {size_in_mb:.2f} MB, Max: {max_size_mb} MB")

                        if size_in_mb > max_size_mb:
                            error_msg = f'{v_message} (uploaded: {size_in_mb:.2f} MB)'

                            _logger.error(
                                f"❌ [File Validation] File too large: {size_in_mb:.2f} MB > {max_size_mb} MB")

                            return {
                                'valid': False,
                                'error': error_msg,
                                'field_label': rules['label']
                            }

                        _logger.info(
                            f"✅ [File Validation] Size valid: {size_in_mb:.2f} MB")

                except Exception as e:
                    _logger.error(f"💥 [File Validation] Size check error: {e}",
                                  exc_info=True)
                    pass


            # Max characters
            elif v_type == 'max_characters':
                if len(str(field_value)) > v_value:
                    return {
                        'valid': False,
                        'error': f'{v_message} (current: {len(str(field_value))})',
                        'field_label': rules['label']
                    }

            # Min value (number)
            elif v_type == 'min_value':
                try:
                    if float(field_value) < v_value:
                        return {
                            'valid': False,
                            'error': f'{v_message} (current: {field_value})',
                            'field_label': rules['label']
                        }
                except (ValueError, TypeError):
                    pass

            # Max value (number)
            elif v_type == 'max_value':
                try:
                    if float(field_value) > v_value:
                        return {
                            'valid': False,
                            'error': f'{v_message} (current: {field_value})',
                            'field_label': rules['label']
                        }
                except (ValueError, TypeError):
                    pass

            # No negative
            elif v_type == 'no_negative':
                try:
                    if float(field_value) < 0:
                        return {
                            'valid': False,
                            'error': v_message,
                            'field_label': rules['label']
                        }
                except (ValueError, TypeError):
                    pass

            # Integer only
            elif v_type == 'integer_only':
                try:
                    if float(field_value) != int(float(field_value)):
                        return {
                            'valid': False,
                            'error': v_message,
                            'field_label': rules['label']
                        }
                except (ValueError, TypeError):
                    pass

            # Max decimal places
            elif v_type == 'max_decimal_places':
                try:
                    str_value = str(float(field_value))
                    if '.' in str_value:
                        decimal_part = str_value.split('.')[1]
                        decimal_part = decimal_part.rstrip('0')
                        if len(decimal_part) > v_value:
                            return {
                                'valid': False,
                                'error': f'{v_message} (current: {len(decimal_part)} places)',
                                'field_label': rules['label']
                            }
                except (ValueError, TypeError):
                    pass

            # Min date
            elif v_type == 'min_date':
                try:
                    from datetime import datetime
                    selected_date = fields.Date.from_string(field_value)
                    min_date = fields.Date.from_string(v_value)

                    if selected_date < min_date:
                        return {
                            'valid': False,
                            'error': f'{v_message} (selected: {selected_date.strftime("%d/%m/%Y")})',
                            'field_label': rules['label']
                        }
                except (ValueError, TypeError) as e:
                    _logger.warning(f"Date validation error for min_date: {e}")
                    pass

            # Max date
            elif v_type == 'max_date':
                try:
                    from datetime import datetime
                    selected_date = fields.Date.from_string(field_value)
                    max_date = fields.Date.from_string(v_value)

                    if selected_date > max_date:
                        return {
                            'valid': False,
                            'error': f'{v_message} (selected: {selected_date.strftime("%d/%m/%Y")})',
                            'field_label': rules['label']
                        }
                except (ValueError, TypeError) as e:
                    _logger.warning(f"Date validation error for max_date: {e}")
                    pass

            # Date range
            elif v_type == 'date_range':
                try:
                    from datetime import datetime
                    selected_date = fields.Date.from_string(field_value)
                    min_date = fields.Date.from_string(validation['min'])
                    max_date = fields.Date.from_string(validation['max'])

                    if not (min_date <= selected_date <= max_date):
                        return {
                            'valid': False,
                            'error': f'{v_message} (selected: {selected_date.strftime("%d/%m/%Y")})',
                            'field_label': rules['label']
                        }
                except (ValueError, TypeError) as e:
                    _logger.warning(
                        f"Date validation error for date_range: {e}")
                    pass

            # Regex pattern
            elif v_type == 'regex_pattern':
                if not re.match(v_value, str(field_value)):
                    return {
                        'valid': False,
                        'error': v_message,
                        'field_label': rules['label']
                    }

            # Unique value
            elif v_type == 'unique':
                domain = [
                    (field_name, '=', field_value),
                    ('company_id', '=', company.id)
                ]

                if self.id:
                    domain.append(('id', '!=', self.id))

                existing = self.search(domain, limit=1)

                if existing:
                    error_msg = f'{v_message} - Value "{field_value}" already exists'
                    if existing.name:
                        error_msg += f' in product "{existing.name}"'
                    if existing.default_code:
                        error_msg += f' (Ref: {existing.default_code})'

                    return {
                        'valid': False,
                        'error': error_msg,
                        'field_label': rules['label'],
                        'existing_product_id': existing.id,
                        'existing_product_name': existing.name or existing.display_name
                    }

        return {'valid': True, 'error': None}

    def _detect_file_type_from_base64(self, base64_string):
        """
        Detect file type from base64 string by checking magic bytes (file signature)
        Returns: file extension (e.g., 'jpg', 'png', 'pdf') or None
        """
        try:
            import base64

            # Decode first few bytes to check signature
            decoded = base64.b64decode(base64_string[:100])

            # File signatures (magic bytes)
            signatures = {
                b'\xFF\xD8\xFF': 'jpg',  # JPEG
                b'\x89PNG\r\n\x1a\n': 'png',  # PNG
                b'GIF87a': 'gif',  # GIF87a
                b'GIF89a': 'gif',  # GIF89a
                b'%PDF': 'pdf',  # PDF
                b'PK\x03\x04': 'zip',  # ZIP (also docx, xlsx)
                b'Rar!': 'rar',  # RAR
                b'\x00\x00\x01\x00': 'ico',  # ICO
                b'BM': 'bmp',  # BMP
                b'RIFF': 'webp',  # WebP/RIFF (need to check further)
                b'\x1f\x8b': 'gz',  # GZIP
                b'PK\x05\x06': 'zip',  # Empty ZIP
                b'PK\x07\x08': 'zip',  # Spanned ZIP
            }

            # Check signatures
            for signature, extension in signatures.items():
                if decoded.startswith(signature):
                    # Special case for WebP
                    if signature == b'RIFF':
                        if b'WEBP' in decoded[:20]:
                            return 'webp'
                        return None

                    _logger.info(
                        f"🔍 [File Detection] Detected {extension} from signature: {signature.hex()}")
                    return extension

            # Check if it's SVG (XML-based, starts with < or whitespace then <)
            try:
                text_start = decoded[:100].decode('utf-8', errors='ignore')
                if '<svg' in text_start.lower() or '<?xml' in text_start.lower():
                    return 'svg'
            except:
                pass

            _logger.warning(
                f"⚠️ [File Detection] Unknown file signature: {decoded[:20].hex()}")
            return None

        except Exception as e:
            _logger.error(f"💥 [File Detection] Error: {e}", exc_info=True)
            return None







