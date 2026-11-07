# -*- coding: utf-8 -*-

import time, pytz
import re
from datetime import datetime, timedelta, timezone, date
from email.policy import default
from markupsafe import Markup
import pytz
import base64
import io
import requests

from lxml import etree
from odoo import models, api, fields, _, tools
from odoo.exceptions import UserError, ValidationError
import traceback, pdb, inspect
from rembg import remove, new_session
from PIL import Image, ImageOps
import onnxruntime as ort
from odoo.tools import drop_view_if_exists
import logging

_logger = logging.getLogger(__name__)


class ManufacturerAttribute(models.Model):
    _name = 'manufacturer.attribute'
    _description = 'Manufacturer Attribute'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, tracking=True)


class BrandAttribute(models.Model):
    _name = 'brand.attribute'
    _description = 'Brand Attribute'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, tracking=True)


class FamilyProducts(models.Model):
    _name = 'family.products'
    _description = 'Family Products'

    product_id = fields.Many2one('product.template', 'Product', required=True)
    default_code = fields.Char('SKU #')
    family_id = fields.Many2one('family.attribute', 'Family')
    mpn_number = fields.Char('MPN')
    status = fields.Selection([('active', 'Active'), ('inactive', 'In Active')], 'Status')
    origin = fields.Char('Origin')
    po_min = fields.Integer('PO Min')
    po_max = fields.Integer('PO Max')
    p65 = fields.Char('P65')
    # attribute1_id = fields.Many2one('product.attribute1','',related='family_id.attribute1_id',)
    attribute1_val = fields.Char('Attribute 1')
    # attribute2_id = fields.Many2one('product.attribute2','',related='family_id.attribute2_id',)
    attribute2_val = fields.Char('Attribute 2')
    # attribute3_id = fields.Many2one('product.attribute3','',related='family_id.attribute3_id',)
    attribute3_val = fields.Char('Attribute 3')
    # attribute4_id = fields.Many2one('product.attribute4','',related='family_id.attribute4_id',)
    attribute4_val = fields.Char('Attribute 4')
    select_sku = fields.Boolean('Select')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    name = fields.Char()
    product_sequence = fields.Char("Sequence")
    attribute_group_ids = fields.Many2many('attribute.group', string='Attribute Group', store=True)
    attribute_family_ids = fields.Many2many('family.attribute', string='Family Attribute', store=True)
    hs_code = fields.Char('HS Code')
    percentage_complete = fields.Float(string="Complete",
                                       help="Percentage of completion (0-100)")

    progress_state = fields.Selection([
        ('partially_completed', 'Partially Completed'),
        ('almost_completed', 'Almost Completed'),
        ('fully_completed', 'Fully Completed'),
        ('not_completed', 'Not Completed'),
        ('incomplete', 'Incomplete')
    ], string="Progress State")

    active_label = fields.Char(string="Status ", default="ENABLED", compute="_compute_active_label")

    image_ids = fields.One2many(
        'product.image',
        'product_variant_id',
        string='Images'
    )
    sku = fields.Char(string='SKU', related="product_tmpl_id.sku", store=True)
    is_sku_manual = fields.Boolean("Different SKU's", related="product_tmpl_id.is_sku_manual")

    is_na = fields.Json(string="IS Na", compute='_compute_is_na')

    @api.depends('is_na', 'family_id')
    def _compute_is_na(self):
        """This method is used to find the field NA or not based on the family"""
        for rec in self:
            sanitize = lambda s: re.sub(r'_+', '_',
                                        re.sub(r'[^a-z0-9_]', '_',
                                               s.lower().replace(' #',
                                                                 '_1').replace(
                                                   '-', ''))).strip('_')
            company_suffix = sanitize(rec.company_id.name or '')

            # Filter dynamic fields created for this company
            all_fields = rec._fields.keys()
            dynamic_fields = [
                field for field in all_fields
                if
                field.startswith('x_') and field.endswith(f'_{company_suffix}')
            ]

            # Get family attribute field names
            family_attribute = rec.family_id.variant_line_ids.mapped(
                'variant_ids')
            family_fields = family_attribute.mapped("original_name")

            # Build JSON structure
            fields_data = {}
            for field in dynamic_fields:
                # Check if field exists in family
                if field in family_fields:
                    fields_data[field] = {
                        "is_na": False}  # Field in family = No (False)
                else:
                    fields_data[field] = {
                        "is_na": True}  # Field NOT in family = Yes (True)

            # Final JSON structure
            result = {
                "product_name": rec.name or '',
                "product_id": rec.id,
                "fields": fields_data
            }

            rec.is_na = result

    @api.depends('active', 'company_id')
    def _compute_active_label(self):
        for record in self:
            record.active_label = "ENABLED" if record.active else "DISABLED"

    @api.depends('product_template_attribute_value_ids')
    def _compute_attribute_group_ids(self):
        self.attribute_group_ids = self.product_template_attribute_value_ids.attribute_id.attribute_group
        self.attribute_family_ids = self.product_template_attribute_value_ids.attribute_id.attribute_group.attribute_family_id

    def _compute_percentage_complete(self):
        for product in self:
            filled_count = 0
            total_count = 0
            if product.family_id:
                attributes = product.family_id.mapped('family_attribute_ids').mapped('attribute_id')
                for attr_rec in attributes:
                    if attr_rec.is_completeness:
                        total_count += 1
                        # Correctly format the field name to replace spaces with underscores
                        field_name = attr_rec.original_name
                        if field_name in product._fields:
                            attribute_value = getattr(product, field_name, None)
                            if isinstance(product._fields[field_name], fields.Boolean):
                                if attribute_value:
                                    filled_count += 1
                            else:
                                if attribute_value not in [False, None, ""]:
                                    filled_count += 1
                        else:
                            # Log or handle missing field (debugging purposes)
                            pass  # Consider adding a debug log here
            required_product_fields = self.env['general.attribute'].sudo().search([('completeness', '=', True),
                                                                                   ('related_field.model_id.model',
                                                                                    '=',
                                                                                    'product.template')])

            if required_product_fields:
                total_count += len(required_product_fields)
                for field in required_product_fields.mapped('related_field').mapped('name'):
                    if getattr(product, field):
                        filled_count += 1
            percentage_complete = (filled_count / total_count * 100) if total_count > 0 else 0
            if percentage_complete >= 70:
                progress_state = 'fully_completed'
            elif percentage_complete >= 55 and percentage_complete < 70:
                progress_state = 'almost_completed'
            elif percentage_complete >= 40 and percentage_complete < 55:
                progress_state = 'partially_completed'
            elif percentage_complete >= 25 and percentage_complete < 40:
                progress_state = 'not_completed'
            else:
                progress_state = 'incomplete'
            if required_product_fields or product.family_id:
                product.with_context(syncing_exist_attrs=True).write({'percentage_complete': percentage_complete,
                                                                      'progress_state': progress_state
                                                                      })
            else:
                product.with_context(syncing_exist_attrs=True).write({'percentage_complete': 0,
                                                                      'progress_state': progress_state})

    def write(self, vals):
        result = super(ProductProduct, self.with_context(lang=self.env.user.product_lang)).write(vals)
        for rec in self:
            if not self.env.context.get('syncing_exist_attrs'):
                rec.with_context(syncing_exist_attrs=True)._compute_percentage_complete()
        return result

    def is_product_sequence(self):
        """Check product sequence exist or not"""
        sequence = self.env['ir.sequence'].sudo().search([
            ('code', '=', 'product.product.product'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return bool(sequence)

    def update_product_sequence(self):
        """Update product sequence for product and product variant continuous"""
        if not self.env['ir.sequence'].sudo().search(
                [('code', '=', 'product.template.product'), ('company_id', 'in', [self.env.company.id])]):
            self.env['ir.sequence'].sudo().create({
                'name': _("Product Sequence"),
                'code': "product.template.product",
                'company_id': self.env.company.id,
                'prefix': "",
                'number_next': 10001,
                'padding': 5,
                'implementation': 'no_gap',
            })
        if not self.is_product_sequence():
            self.env['ir.sequence'].sudo().create({
                'name': _("Product Product Sequence"),
                'code': "product.product.product",
                'company_id': self.env.company.id,
                'prefix': "",
                'padding': 5,
                'implementation': 'no_gap',
            })
        for rec in self:
            if rec.has_configurable_attributes:
                rec.product_sequence = self.env['ir.sequence'].sudo().next_by_code('product.template.product')
            else:
                rec.product_sequence = self.env['ir.sequence'].sudo().next_by_code('product.product.product')

    @api.model_create_multi
    def create(self, vals):
        records = super(ProductProduct, self).create(vals)
        records.update_product_sequence()
        return records

    @api.model
    def init(self):
        self.env.cr.execute("""
                    DROP INDEX IF EXISTS product_product_combination_unique
                """)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name = fields.Char()
    product_sequence = fields.Char("Sequence")
    hs_code = fields.Char('HS Code')
    mpn_number = fields.Char('MPN')
    status = fields.Selection([('active', 'Active'), ('inactive', 'In Active')], 'Status')
    origin = fields.Char('Origin')
    po_min = fields.Integer('PO Min')
    po_max = fields.Integer('PO Max')
    p65 = fields.Char('P65')
    # attribute1_id = fields.Many2one('product.attribute1','Attribute 1')
    attribute1_val = fields.Char('Value 1')
    # attribute2_id = fields.Many2one('product.attribute2','Attribute 2')
    attribute2_val = fields.Char('Value 2')
    # attribute3_id = fields.Many2one('product.attribute3','Attribute 3')
    attribute3_val = fields.Char('Value 3')
    # attribute4_id = fields.Many2one('product.attribute4','Attribute 4')
    attribute4_val = fields.Char('Value 4')
    active_label = fields.Char(string="Status ", compute="_compute_active_label")

    readable_variant_names = fields.Char(string="Variants")
    family_id = fields.Many2one('family.attribute', string='Family', readonly=True)
    sku = fields.Char(string='SKU')
    is_sku_manual = fields.Boolean("Different SKU's")
    pim_is_published = fields.Boolean("PIM Published")
    brand_id = fields.Many2one('product.brand', string='Brand')
    supplier_id = fields.Many2one('supplier.info', string='Supplier')
    category_id = fields.Many2one('pim.category', string='Category')
    pim_category_ids = fields.Many2many('pim.category', 'product_category_many_rel', 'product_id', 'category_id',
                                        string='Category')

    parent_id = fields.Many2one(
        'product.create',
        string='Parent Group',
        ondelete='cascade',
    )

    product_master_id = fields.Many2one(
        'product.create.master',
        string='Parent Group ',
        ondelete='cascade',
    )

    product_parent_id = fields.Many2one(
        'product.template',
        string='Parent-Group',
        ondelete='cascade',
    )
    product_tmplt_ids = fields.One2many(
        'product.template',
        'product_parent_id',
        string='Sub-groups'
    )

    is_update_from_attribute = fields.Boolean(string='Created from attribute')
    percentage_complete = fields.Float(string="Complete",
                                       help="Percentage of completion (0-100)")

    progress_state = fields.Selection([
        ('partially_completed', 'Partially Completed'),
        ('almost_completed', 'Almost Completed'),
        ('fully_completed', 'Fully Completed'),
        ('not_completed', 'Not Completed'),
        ('incomplete', 'Incomplete')
    ], string="Progress State")
    has_variant = fields.Boolean(string="Has Varint Product")
    is_variant = fields.Boolean(string='Variant Product')
    variant_id = fields.Many2one('family.variant.line', string='Family Variant')
    is_variant_values_updated = fields.Boolean(default=False, string='Is Variant value updated')
    product_attr_values_id = fields.Many2many('product.attribute.value', 'attr_value_id', 'products_id',
                                              string='Attribute Values ', readonly=True)
    product_attr_ids = fields.One2many('product.attribute', 'products_id', string='Attributes')
    is_variant_update = fields.Boolean(string='Variant updated', default=False)
    image_1 = fields.Image("Image1", max_width=1920, max_height=1920, compute="_compute_first_image",
                           store=False)
    image_2 = fields.Image("Image2", max_width=1920, max_height=1920)
    image_3 = fields.Image("Image3", max_width=1920, max_height=1920)
    image_4 = fields.Image("Image4", max_width=1920, max_height=1920)
    image_5 = fields.Image("Image5", max_width=1920, max_height=1920)
    image_6 = fields.Image("Image6", max_width=1920, max_height=1920)
    image_7 = fields.Image("Image7", max_width=1920, max_height=1920)
    image_8 = fields.Image("Image8", max_width=1920, max_height=1920)
    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")
    image_ids = fields.One2many(
        'product.image',
        'product_tmpl_id',
        string='Images/Video'
    )
    image_url = fields.Char("Image URL")

    select_product_variant_id = fields.Many2one("product.product",
                                                string="Product Variant",
                                                domain="[('id','in', product_variant_ids)]")

    is_na = fields.Json(string="IS Na", compute="_compute_is_na")

    quality_type = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E')], string="Quality Type",
                                    default='a')


    @api.depends('is_na', 'family_id')
    def _compute_is_na(self):
        """This method is used to find the field NA or not based on the family"""
        for rec in self:
            sanitize = lambda s: re.sub(r'_+', '_',
                                        re.sub(r'[^a-z0-9_]', '_',
                                               s.lower().replace(' #',
                                                                 '_1').replace(
                                                   '-', ''))).strip('_')
            company_suffix = sanitize(rec.company_id.name or '')

            # Filter dynamic fields created for this company
            all_fields = rec._fields.keys()
            dynamic_fields = [
                field for field in all_fields
                if
                field.startswith('x_') and field.endswith(f'_{company_suffix}')
            ]

            # Get family attribute field names
            family_fields = rec.family_id.family_attribute_ids.mapped(
                'attribute_id.original_name')

            # Build JSON structure
            fields_data = {}
            for field in dynamic_fields:
                # Check if field exists in family
                if field in family_fields:
                    fields_data[field] = {
                        "is_na": False}  # Field in family = No (False)
                else:
                    fields_data[field] = {
                        "is_na": True}  # Field NOT in family = Yes (True)

            # Final JSON structure
            result = {
                "product_name": rec.name or '',
                "product_id": rec.id,
                "fields": fields_data
            }

            rec.is_na = result

    def get_attributes(self):
        return self.env['product.attribute'].search(
            [('original_name', 'in', list(self._fields.keys()))])

    @api.model
    def get_sku_by_id(self, record_id):
        template = self.browse(record_id)
        if not template.exists():
            return {
                'error': f'Product template with ID {record_id} not found'
            }

        # Collect SKUs from variants
        skus = []
        for variant in template.product_variant_ids:
            skus.append({
                'variant_id': variant.id,
                'sku': variant.default_code or 'No SKU',
            })

        return {
            'product_id': template.id,
            'product_name': template.name,
            'skus': skus
        }

    # Add these methods to your ProductTemplate class

    @api.model
    def get_product_info(self, record_id, info_type='all'):
        """
        Unified method to get product information based on request type
        info_type: 'sku', 'details', 'all', 'info', 'count'
        """
        product = self.sudo().browse(record_id)

        if not product.exists():
            return {"error": f"Product with ID {record_id} not found"}

        # Base product info
        base_info = {
            "product_name": product.name,
            "sku": product.default_code or "No SKU",
            "default_code": product.default_code or "No Code",
            "category": product.categ_id.name if product.categ_id else "No Category",
            "type": product.type or "N/A",
            "description": product.description_sale or product.description or "No Description",
        }

        # Return specific information based on request type
        if info_type == 'sku':
            return {
                "product_name": base_info["product_name"],
                "sku": base_info["sku"]
            }
        elif info_type == 'details' or info_type == 'all' or info_type == 'info':
            return base_info
        else:
            return base_info

    # Model side
    @api.model
    def get_product_count(self, category_name=None):
        print("Entered get_product_count with:", category_name)
        domain = []
        if category_name:
            stop_words = ["my", "the", "company", "category"]
            clean_name = category_name.strip().strip('"')

            print("Cleaned category_name:", clean_name)

            if clean_name:
                domain = [('company_id.name', 'ilike', clean_name)]

        count = self.sudo().search_count(domain)
        print("Search domain:", domain, "-> Count:", count)
        return count

    # @api.model
    # def get_details_by_id(self, record_id):
    #     product = self.sudo().search([('pim_id', '=', record_id)], limit=1)
    #     if not product:
    #         return {"details": "Product not found"}
    #     return {
    #         "product_name": product.name,
    #         "sku": product.sku,
    #         "description": product.description or "",
    #         "default_code": product.default_code or "",
    #         "category": product.categ_id.name if product.categ_id else "",
    #         "type": product.type,
    #     }

    @api.model
    def get_details_by_id(self, record_id):
        product = self.sudo().browse(record_id)
        if product.exists():
            return {
                "product_name": product.name,
                "sku": product.default_code or None,
                "default_code": product.default_code or None,
                "category": product.categ_id.name if product.categ_id else None,
                "type": product.type or None,
                "description": product.description_sale or product.description or None,
            }
        return {}

    @api.depends('image_url', 'image_ids.image_1920', 'image_ids.is_primary')
    def _compute_first_image(self):
        for record in self:
            primary_image = record.image_ids.filtered(lambda i: i.is_primary)[:1]
            if primary_image.image_1920:
                record.image_1 = primary_image.image_1920
                record.image_1920 = primary_image.image_1920
            else:
                record.image_1 = False

    company_id = fields.Many2one('res.company', required=True, readonly=False,
                                 default=lambda self: self.env.company)

    def _prepare_history_log(self, vals, is_create=False):
        for rec in self:
            current_datetime_utc = fields.Datetime.now()
            user_tz = self.env.user.tz or 'UTC'
            current_datetime = current_datetime_utc.astimezone(
                pytz.timezone(user_tz)
            ).strftime("%d/%m/%Y %H:%M:%S")
            user_name = self.env.user.display_name
            changes = []

            # Skip logging if update happens instantly after creation
            if rec.history_log and not is_create:
                last_log = rec.history_log.split('on ')[-1].split('</small>')[0]
                if last_log == current_datetime:
                    continue

            if not is_create and rec.create_date:
                time_diff = (fields.Datetime.now() - rec.create_date).total_seconds()
                if time_diff < 1:
                    continue

            excluded_fields = {
                'id', 'write_date', 'write_uid', 'create_date',
                'create_uid', 'history_log'
            }

            for field_name, new_value in vals.items():
                if field_name in excluded_fields:
                    continue

                field = rec._fields.get(field_name)
                if not field:
                    continue

                field_type = field.type
                field_label = field.string
                old_value = 'N/A' if is_create else getattr(rec, field_name, 'N/A')

                # ---------- Many2one ----------
                if field_type == 'many2one':
                    old_display = 'N/A' if is_create else (old_value.display_name if old_value else 'N/A')
                    new_display = self.env[field.comodel_name].browse(
                        new_value).display_name if new_value else 'N/A'

                    if not is_create and old_value.id if old_value else False == new_value:
                        continue  # skip if no change

                    old_value, new_value = old_display, new_display

                # ---------- One2many ----------
                elif field_type == 'one2many' and not is_create:
                    for command in new_value:
                        if command[0] == 1:  # update
                            sub_rec = rec[field_name].browse(command[1])
                            for subfield, subval in command[2].items():
                                sub_old = getattr(sub_rec, subfield, 'N/A')
                                if sub_old != subval:
                                    changes.append(f"""
                                     <li>
                                         <strong>{field_label} ({subfield})</strong><br>
                                         <span style='color: red;'>Old value:</span> {sub_old}
                                         &nbsp;&nbsp;&nbsp;
                                         <span style='color: green;'>New value:</span> {subval}
                                     </li>
                                 """)
                        elif command[0] == 0:  # create
                            changes.append(f"""
                             <li><strong>Added to {field_label}:</strong> {command[2].get('name', 'New Record')}</li>
                         """)
                        elif command[0] == 2:  # delete
                            deleted_rec = rec[field_name].browse(command[1])
                            changes.append(f"""
                             <li><strong>Removed from {field_label}:</strong> {deleted_rec.display_name}</li>
                         """)
                    continue

                # ---------- Many2many ----------
                elif field_type == 'many2many' and not is_create:
                    old_ids = rec[field_name].ids
                    new_ids = []

                    if isinstance(new_value, list) and new_value and isinstance(new_value[0], (list, tuple)):
                        for command in new_value:
                            if command[0] == 6:
                                new_ids = command[2]
                            elif command[0] == 4:
                                new_ids.append(command[1])
                            elif command[0] == 3 and command[1] in new_ids:
                                new_ids.remove(command[1])
                    else:
                        new_ids = new_value if isinstance(new_value, (list, tuple)) else []

                    added = set(new_ids) - set(old_ids)
                    removed = set(old_ids) - set(new_ids)

                    if added:
                        added_names = self.env[field.comodel_name].browse(added).mapped('display_name')
                        changes.append(f"""
                         <li><strong>Added to {field_label}:</strong> {', '.join(added_names)}</li>
                     """)
                    if removed:
                        removed_names = self.env[field.comodel_name].browse(removed).mapped('display_name')
                        changes.append(f"""
                         <li><strong>Removed from {field_label}:</strong> {', '.join(removed_names)}</li>
                     """)
                    continue

                # ---------- Boolean ----------
                if isinstance(old_value, bool):
                    old_value = 'Yes' if old_value else 'No'
                if isinstance(new_value, bool):
                    new_value = 'Yes' if new_value else 'No'

                # ---------- Skip if unchanged ----------
                if not is_create and str(old_value) == str(new_value):
                    continue

                # ---------- Log change ----------
                changes.append(f"""
                 <li>
                     <strong>{field_label}</strong><br>
                     <span style='color: red;'>Old value:</span> {old_value}
                     &nbsp;&nbsp;&nbsp;
                     <span style='color: green;'>New value:</span> {new_value}
                 </li>
             """)

            if changes:
                action_text = 'Created by' if is_create else 'Updated by'
                user_info = f"<small>{action_text} <strong>{user_name}</strong> on {current_datetime}</small>"
                full_message = f"""
                 <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                     {user_info}
                     <ul style="list-style-type: none; padding-left: 0;">{''.join(changes)}</ul>
                 </div>
             """
                rec.with_context(skip_history_log=True).write({
                    'history_log': tools.html_sanitize(full_message) + (rec.history_log or '')
                })

    def action_open_media_upload_wizard(self):
        """
        Placeholder method to satisfy XML validation.
        Use the new Media Widget below instead.
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Feature Updated',
                'message': 'Please use the new Media Widget section below to upload files.',
                'type': 'info',
                'sticky': False,
            }
        }

    # def _prepare_history_log(self, vals, is_create=False):
    #      for rec in self:
    #           current_datetime_utc = fields.Datetime.now()
    #           user_tz = self.env.user.tz or 'UTC'
    #           current_datetime = current_datetime_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
    #           user_name = self.env.user.display_name
    #           changes = []
    #
    #           # Skip logging if this is an update immediately after creation
    #           if rec.history_log and not is_create:
    #                last_log = rec.history_log.split('on ')[-1].split('</small>')[0]
    #                if last_log == current_datetime:
    #                     continue  # Skip if timestamp matches the last log
    #
    #           # Additional check: Skip if update happens within 1 second of creation
    #           if not is_create and rec.create_date:
    #                time_diff = (fields.Datetime.now() - rec.create_date).total_seconds()
    #                if time_diff < 1:  # Adjust this threshold as needed
    #                     continue
    #
    #           excluded_fields = {'id', 'write_date', 'write_uid', 'create_date', 'create_uid', 'history_log'}
    #           for field_name in vals.keys():
    #                if field_name in excluded_fields:
    #                     continue
    #
    #                field = rec._fields.get(field_name)
    #                if not field:
    #                     continue
    #
    #                field_type = field.type
    #                field_label = field.string
    #
    #                old_value = 'N/A' if is_create else getattr(rec, field_name, 'N/A')
    #                new_value = vals[field_name]
    #
    #                # Skip if no change occurred (for write only)
    #                if not is_create and old_value == new_value:
    #                     continue
    #
    #                # Handle relational fields
    #                if field_type == 'many2one':
    #                     old_value = 'N/A' if is_create else (old_value.display_name if old_value else 'N/A')
    #                     new_value = self.env[field.comodel_name].browse(new_value).display_name if new_value else 'N/A'
    #
    #                elif field_type == 'one2many' and not is_create:
    #                     for command in new_value:
    #                          if command[0] == 1:  # Update
    #                               sub_rec = rec[field_name].browse(command[1])
    #                               for subfield, subval in command[2].items():
    #                                    sub_old = getattr(sub_rec, subfield, 'N/A')
    #                                    if sub_old != subval:
    #                                         changes.append(f"""
    #                                     <li>
    #                                         <strong>{field_label} ({subfield})</strong><br>
    #                                         <span style='color: red;'>Old value:</span> {sub_old}
    #                                              
    #                                         <span style='color: green;'>New value:</span> {subval}
    #                                     </li>
    #                                 """)
    #                          elif command[0] == 0:  # Create
    #                               changes.append(f"""
    #                             <li><strong>Added to {field_label}:</strong> {command[2].get('name', 'New Record')}</li>
    #                         """)
    #                          elif command[0] == 2:  # Delete
    #                               deleted_rec = rec[field_name].browse(command[1])
    #                               changes.append(f"""
    #                             <li><strong>Removed from {field_label}:</strong> {deleted_rec.display_name}</li>
    #                         """)
    #                     continue
    #
    #                elif field_type == 'many2many' and not is_create:
    #                     old_ids = rec[field_name].ids  # Current IDs before update
    #                     # Handle many2many commands in vals
    #                     new_ids = []
    #                     if isinstance(new_value, list) and new_value and isinstance(new_value[0], (list, tuple)):
    #                          # Process command list like [(6, 0, [ids])] or [(4, id), ...]
    #                          for command in new_value:
    #                               if command[0] == 6:  # Replace with new list of IDs
    #                                    new_ids = command[2]
    #                               elif command[0] == 4:  # Add an ID
    #                                    new_ids.append(command[1])
    #                               elif command[0] == 3:  # Remove an ID
    #                                    if command[1] in new_ids:
    #                                         new_ids.remove(command[1])
    #                     else:
    #                          # Assume it's a direct list of IDs
    #                          new_ids = new_value if isinstance(new_value, (list, tuple)) else []
    #
    #                     # Calculate added and removed IDs
    #                     added = set(new_ids) - set(old_ids)
    #                     removed = set(old_ids) - set(new_ids)
    #
    #                     if added:
    #                          added_names = self.env[field.comodel_name].browse(added).mapped('display_name')
    #                          changes.append(f"""
    #                         <li><strong>Added to {field_label}:</strong> {', '.join(added_names)}</li>
    #                     """)
    #                     if removed:
    #                          removed_names = self.env[field.comodel_name].browse(removed).mapped('display_name')
    #                          changes.append(f"""
    #                         <li><strong>Removed from {field_label}:</strong> {', '.join(removed_names)}</li>
    #                     """)
    #                     continue
    #
    #                # Handle boolean values
    #                if isinstance(old_value, bool):
    #                     old_value = 'Yes' if old_value else 'No'
    #                if isinstance(new_value, bool):
    #                     new_value = 'Yes' if new_value else 'No'
    #
    #                # Format the change entry
    #                changes.append(f"""
    #                 <li>
    #                     <strong>{field_label}</strong><br>
    #                     <span style='color: red;'>Old value:</span> {old_value}
    #                          
    #                     <span style='color: green;'>New value:</span> {new_value}
    #                 </li>
    #             """)
    #
    #           if changes:
    #                action_text = 'Created by' if is_create else 'Updated by'
    #                user_info = f"<small>{action_text} <strong>{user_name}</strong> on {current_datetime}</small>"
    #                full_message = f"""
    #                     <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
    #                     {user_info}
    #                            <ul style="list-style-type: none; padding-left: 0;">{''.join(changes)}</ul>
    #                     </div>
    #                    """
    #                 # rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')
    #                rec.with_context(skip_history_log=True).write({
    #                   'history_log': tools.html_sanitize(full_message) + (rec.history_log or '')
    #                })

    def update_product_sequence(self):
        """Update product sequence for product and product variant continuous"""
        if not self.env['ir.sequence'].sudo().search(
                [('code', '=', 'product.template.product'), ('company_id', 'in', [self.env.company.id])]):
            self.env['ir.sequence'].sudo().create({
                'name': _("Product Sequence"),
                'code': "product.template.product",
                'company_id': self.env.company.id,
                'prefix': "",
                'number_next': 10001,
                'padding': 5,
                'implementation': 'no_gap',
            })
        for rec in self:
            rec.product_sequence = self.env['ir.sequence'].sudo().next_by_code('product.template.product')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProductTemplate, self).create(vals_list)
        records.update_product_sequence()
        for rec, vals in zip(records, vals_list):
            if vals.get('image_url'):
                self.env['product.image'].create({
                    'name': rec.name,
                    'image_url': vals['image_url'],
                    'product_tmpl_id': rec.id,
                    'is_primary': True,
                })
            rec.with_context(skip_history_log=True)._prepare_history_log(vals, is_create=True)
        return records

    def write(self, vals):
        if not self.env.context.get('skip_history_log'):
            self._prepare_history_log(vals, is_create=False)
        self.attribute_validation_conditions(vals)
        result = super(ProductTemplate, self.with_context(lang=self.env.user.product_lang)).write(vals)
        for rec in self:
            # --- Sync update percentage if not already syncing ---
            if not self.env.context.get('syncing_exist_attrs'):
                rec.with_context(syncing_exist_attrs=True)._compute_percentage_complete()
        return result

    def attribute_validation_conditions(self, vals):
        # pattern = "^(?=.*[a-zA-Z0-9])[A-Za-z0-9 ]+$"
        pattern = r"^(?=.*[A-Za-z])[A-Za-z0-9 ]+$"

        for rec in self:
            for attr in rec.family_id.exist_attribute_ids:
                if attr.original_name in vals:
                    if attr.alpha_numeric_value == 'yes':
                        # print("vals  == ", vals[attr.original_name])
                        if vals[attr.original_name] and not re.match(pattern, vals[attr.original_name]):
                            raise ValidationError("Attribute value should be AlphaNumeric")
                    if attr.unique_value == 'yes':
                        field_val_count = self.env['product.template'].search(
                            [(attr.original_name, '=ilike', vals[attr.original_name]),
                             ('company_id', '=', rec.company_id.id)])
                        if len(field_val_count) > 1:
                            raise ValidationError(_('%s value already exist.', attr.name))

                #     if attr.is_mandatory and not vals.get(attr.original_name):
                #         raise ValidationError(_("%s is required.") % attr.name)
                # else:
                #     print("else =======")
                #     # Case: attribute not in vals but is mandatory
                #     if attr.is_mandatory and not getattr(rec, attr.original_name, False):
                #         raise ValidationError(_("%s is required.") % attr.name)

    def _compute_products_ids(self):
        for record in self:
            record.product_tmplt_ids = self.env['product.template'].search(
                [('company_id', '=', self.env.company.id)])

    def action_back_to_product_menu(self):
        return {
            'name': 'products',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'views': [
                (self.env.ref('pim_ext.view_product_management_tree').id, 'list'),
                (self.env.ref('pim_ext.view_product_management_kanban').id, 'kanban'),
                (self.env.ref('pim_ext.view_product_creation_split_view_custom').id, 'form'),
            ],
            'domain': [('company_id', 'in', [self.env.company.id])],
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
            }
        }

    # @api.depends('family_id')
    def _compute_percentage_complete(self):
        for product in self:
            filled_count = 0
            total_count = 0
            if product.family_id:
                attributes = product.family_id.mapped('family_attribute_ids').mapped('attribute_id')
                for attr_rec in attributes:
                    if attr_rec.is_completeness:
                        total_count += 1
                        # Correctly format the field name to replace spaces with underscores
                        field_name = attr_rec.original_name
                        if field_name in product._fields:
                            attribute_value = getattr(product, field_name, None)
                            if isinstance(product._fields[field_name], fields.Boolean):
                                if attribute_value:
                                    filled_count += 1
                            else:
                                if attribute_value not in [False, None, ""]:
                                    filled_count += 1
                        else:
                            # Log or handle missing field (debugging purposes)
                            pass  # Consider adding a debug log here
            required_product_fields = self.env['general.attribute'].sudo().search([('completeness', '=', True),
                                                                                   ('related_field.model_id.model',
                                                                                    '=',
                                                                                    'product.template')])

            if required_product_fields:
                total_count += len(required_product_fields)
                for field in required_product_fields.mapped('related_field').mapped('name'):
                    if getattr(product, field):
                        filled_count += 1
            percentage_complete = (filled_count / total_count * 100) if total_count > 0 else 0
            if percentage_complete >= 70:
                progress_state = 'fully_completed'
            elif percentage_complete >= 55 and percentage_complete < 70:
                progress_state = 'almost_completed'
            elif percentage_complete >= 40 and percentage_complete < 55:
                progress_state = 'partially_completed'
            elif percentage_complete >= 25 and percentage_complete < 40:
                progress_state = 'not_completed'
            else:
                progress_state = 'incomplete'
            if required_product_fields or product.family_id:
                product.with_context(syncing_exist_attrs=True).write({'percentage_complete': percentage_complete,
                                                                      'progress_state': progress_state
                                                                      })
            else:
                product.with_context(syncing_exist_attrs=True).write({'percentage_complete': 0,
                                                                      'progress_state': progress_state})

    def update_variant_values(self):
        attribute_value = self.variant_id.variant_ids[:1]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'attribute.variant.values.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attribute_family_id': self.family_id.id,
                        'default_product_id': self.id,
                        'default_variant_id': self.variant_id.id,
                        'default_attribute_id': attribute_value.id if attribute_value else False,
                        'no_breadcrumbs': True,
                        },
        }

    @api.depends('product_variant_ids')
    def _compute_readable_variant_names(self):
        for template in self:
            if template.product_variant_ids:
                template.readable_variant_names = ', '.join(template.product_variant_ids.mapped('name'))
            else:
                template.readable_variant_names = "N/A"

    @api.depends('active')
    def _compute_active_label(self):
        for record in self:
            record.active_label = "ENABLED" if record.active else "DISABLED"

    def create_pim_products(self):
        # all_product_ids = self.env['product.template'].search([], order='create_date desc').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'CREATE PRODUCT',
            'res_model': 'product.create.wizard',
            'view_mode': 'form',
            # 'view_id': self.env.ref('pim_ext.view_product_create_wizard_form').id,
            'context': {'no_breadcrumbs': True,
                        "default_product_create_type": "none",
                        "default_model": "product.template",
                        # 'default_master_products_ids': all_product_ids,
                        },
            'target': 'current',
        }

    def save_product_rec(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.template',
            'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
            'res_id': self.id,
            'context': {'no_breadcrumbs': True},
            'target': 'current',
        }

    def custom_product_open_form_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
            'context': {'no_breadcrumbs': True,
                        },
            'res_id': self.id,
        }

    def custom_product_open_default_form_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_mode': 'form',
            'view_id': self.env.ref('product.product_template_only_form_view').id,
            'context': {'no_breadcrumbs': True,
                        },
            'res_id': self.id,
            'target': 'new',
        }

    def custom_product_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id, 'no_breadcrumbs': True, },
        }

    def open_category_wizard(self):
        active_id = self.env.context.get('active_ids')
        # catgeory = self.env['pim.category'].search([])
        # res['category_ids'] = [(6, 0, catgeory.ids)]
        return {
            'name': 'Add Category',
            'type': 'ir.actions.act_window',
            'res_model': 'category.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_ids': active_id, },
        }

    # Duplication Methods
    def copy(self, default=None):
        """
        Override copy to prevent logging during duplication.
        Affects standard Odoo "Duplicate" action.
        """
        default = dict(default or {})
        ctx = dict(
            self.env.context,
            skip_history_log=True,
            tracking_disable=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
            create_product_product=False,
        )
        return super(ProductTemplate, self.with_context(ctx)).copy(default)

    def duplicate_product_with_sku(self, new_sku=False):
        self.ensure_one()
        ProductProduct = self.env['product.product']
        has_custom_sku = 'sku' in ProductProduct._fields

        if not new_sku:
            new_sku = self._compute_next_sku_for_product(self)

        ctx = self._prepare_duplication_context()

        new_vals = self._prepare_product_values(new_sku, ctx)

        return self._create_duplicate_product(new_vals, new_sku)

    @api.model
    def bulk_duplicate_products(self, record_ids, res_model):
        results = {
            'success_count': 0,
            'failed_count': 0,
            'last_duplicated_id': None,
            'errors': [],
        }

        if not record_ids:
            return results

        Model = self.env[res_model]

        for record_id in record_ids:
            try:
                record = Model.browse(record_id)
                if not record.exists():
                    raise UserError(_("Record ID %s not found in %s") % (record_id, res_model))

                if res_model == 'product.template':
                    new_id = self._duplicate_template_record(record)
                elif res_model == 'product.product':
                    new_id = self._duplicate_variant_record(record)
                else:
                    raise UserError(_("Unsupported model: %s") % res_model)

                if new_id:
                    results['success_count'] += 1
                    results['last_duplicated_id'] = new_id

            except Exception as e:
                _logger.error(
                    "Failed to duplicate %s %s: %s",
                    res_model,
                    record_id,
                    e,
                    exc_info=True,
                )
                results['failed_count'] += 1
                results['errors'].append({
                    'record_id': record_id,
                    'error': str(e),
                })

        return results

    def _duplicate_template_record(self, template):
        """
        Duplicate a product template record and:
          - compute new SKU
          - backup original images
          - restore images to new record
          - write history
        """
        original_data = self._get_original_product_data(template)
        new_sku = self._compute_next_sku_for_product(template)
        backup_images = self._backup_product_images(template)

        new_product_id = template.duplicate_product_with_sku(new_sku)

        if new_product_id:
            self._write_duplication_history(new_product_id, original_data)
            self._restore_product_images(new_product_id, backup_images)

        return new_product_id

    def _duplicate_variant_record(self, variant):
        """
        Duplicate a product variant by duplicating its template.
        Returns new template ID.
        """
        if not variant.product_tmpl_id:
            raise UserError(_("Product variant has no template"))
        return self._duplicate_template_record(variant.product_tmpl_id)

    def _compute_next_sku_for_product(self, product):
        ProductProduct = self.env['product.product']
        has_custom_sku = 'sku' in ProductProduct._fields

        source_sku = self._get_source_sku(product, has_custom_sku)

        if not source_sku:
            # Fallback when literally nothing exists
            return f"COPY-{product.id}"

        base_sku = self._extract_base_sku(source_sku)
        max_suffix = self._get_max_suffix_for_base(base_sku, has_custom_sku)

        # If no numeric suffix found at all, start with 1
        next_suffix = (max_suffix + 1) if max_suffix is not None else 1
        return f"{base_sku}-{next_suffix}"

    def _get_source_sku(self, product, has_custom_sku):
        """
        Retrieve source SKU from:
          1) template default_code
          2) template sku (if exists)
          3) first variant default_code
          4) first variant sku
        """
        source_sku = product.default_code

        if (not source_sku) and has_custom_sku and 'sku' in product._fields:
            source_sku = product.sku

        if not source_sku:
            ProductProduct = self.env['product.product']
            first_variant = ProductProduct.search(
                [('product_tmpl_id', '=', product.id)],
                limit=1,
            )
            if first_variant:
                source_sku = first_variant.default_code
                if (not source_sku) and has_custom_sku:
                    source_sku = first_variant.sku

        return source_sku

    def _extract_base_sku(self, sku):
        """
        Extract base SKU without trailing numeric '-N' suffix.
        E.g. ABC-1 -> ABC, ABC-001 -> ABC, ABC-XYZ -> ABC-XYZ
        """
        last_dash_index = sku.rfind('-')
        if last_dash_index == -1:
            return sku

        possible_suffix = sku[last_dash_index + 1:]
        if possible_suffix.isdigit():
            return sku[:last_dash_index]

        return sku

    def _build_sku_search_domain(self, base_sku, has_custom_sku):
        """
        Domain + fields used to scan existing SKUs that start with base_sku.
        """
        if has_custom_sku:
            domain = ['|',
                      ('default_code', '=like', f'{base_sku}%'),
                      ('sku', '=like', f'{base_sku}%')]
            fields_to_read = ['default_code', 'sku']
        else:
            domain = [('default_code', '=like', f'{base_sku}%')]
            fields_to_read = ['default_code']
        return domain, fields_to_read

    def _get_max_suffix_for_base(self, base_sku, has_custom_sku):
        """
        Scan product.product and return the max numeric suffix for codes like:
          base_sku, base_sku-1, base_sku-2, ...
        Returns:
          - int or None (if nothing found)
        """
        ProductProduct = self.env['product.product']
        domain, fields_to_read = self._build_sku_search_domain(base_sku, has_custom_sku)
        existing_products = ProductProduct.search_read(domain, fields_to_read)

        max_suffix = None

        for rec in existing_products:
            codes_to_check = [rec.get('default_code')]
            if has_custom_sku:
                codes_to_check.append(rec.get('sku'))

            for code in codes_to_check:
                if not code:
                    continue

                if code == base_sku:
                    if max_suffix is None:
                        max_suffix = 0
                    continue

                if code.startswith(f"{base_sku}-"):
                    suffix_part = code[len(base_sku) + 1:]
                    if suffix_part.isdigit():
                        val = int(suffix_part)
                        max_suffix = val if max_suffix is None else max(max_suffix, val)

        return max_suffix

    def _prepare_duplication_context(self):
        """
        Prepare context for product duplication (no chatter / no tracking).
        """
        ctx = dict(self.env.context)
        ctx.pop('create_product_product', None)
        ctx.update({
            'skip_history_log': True,
            'tracking_disable': True,
            'mail_create_nosubscribe': True,
            'mail_notrack': True,
        })
        return ctx

    def _prepare_product_values(self, new_sku, ctx):
        """
        Prepare values for new product.template creation using copy_data
        with a safe fallback.
        """
        default_vals = {
            'name': f"{self.name} (Copy)",
            'default_code': new_sku,
        }
        if 'sku' in self._fields:
            default_vals['sku'] = new_sku

        try:
            vals_list = self.with_context(ctx).copy_data(default=default_vals)
            new_vals = vals_list[0] if vals_list else default_vals
        except Exception as e:
            _logger.warning("copy_data failed on product.template %s: %s. Using minimal vals.", self.id, e)
            new_vals = {
                'name': f"{self.name} (Copy)",
                'default_code': new_sku,
                'categ_id': self.categ_id.id,
                'uom_id': self.uom_id.id,
            }
            if 'sku' in self._fields:
                new_vals['sku'] = new_sku

        self._remove_problematic_fields(new_vals)
        return new_vals

    def _remove_problematic_fields(self, vals):
        """
        Remove fields that cause crashes or unwanted duplication behavior.
        """
        fields_to_remove = [
            'product_template_image_ids',
            'product_image_ids',
            'website_image_ids',
            'attribute_line_ids',
            'product_variant_ids',
            'image_1920',
            'image_1024',
            'image_512',
            'image_256',
            'image_128',
        ]
        for field in fields_to_remove:
            vals.pop(field, None)

    def _create_duplicate_product(self, new_vals, new_sku):
        """
        Create duplicate template, ensure variant exists, sync variant SKU.
        """
        ctx = self._prepare_duplication_context()
        try:
            new_product_tmpl = self.env['product.template'].with_context(ctx).create(new_vals)

            variant = self._ensure_variant_exists(new_product_tmpl)
            if variant:
                self._update_variant_sku(variant, new_sku)

            return new_product_tmpl.id

        except Exception as e:
            _logger.error("Error duplicating product.template %s: %s", self.id, e, exc_info=True)
            raise

    def _ensure_variant_exists(self, product_tmpl):
        """
        Ensure there is at least one variant for the template.
        """
        Variant = self.env['product.product']
        variants = Variant.with_context(active_test=False).search([
            ('product_tmpl_id', '=', product_tmpl.id)
        ])

        if not variants and hasattr(product_tmpl, '_create_variant_ids'):
            product_tmpl._create_variant_ids()
            variants = Variant.with_context(active_test=False).search([
                ('product_tmpl_id', '=', product_tmpl.id)
            ])

        return variants[:1] and variants[0] or None

    def _update_variant_sku(self, variant, new_sku):
        """
        Update variant with new SKU values.
        """
        ProductProduct = self.env['product.product']
        has_custom_sku = 'sku' in ProductProduct._fields

        update_vals = {'default_code': new_sku}
        if has_custom_sku:
            update_vals['sku'] = new_sku

        variant.write(update_vals)

    def _get_original_product_data(self, product):
        """Get original product data for history logging."""
        return {
            'name': product.name,
            'default_code': product.default_code or '',
        }

    def _backup_product_images(self, product):
        """Backup product images before duplication."""
        ProductImage = self.env['product.image']
        images = ProductImage.search([('product_tmpl_id', '=', product.id)])

        backup_data = []
        for img in images:
            backup_data.append({
                'name': img.name,
                'image_1920': img.image_1920,
                'is_primary': img.is_primary,
                'sequence': img.sequence,
            })
        return backup_data

    def _write_duplication_history(self, new_product_id, original_data):
        """Write duplication history to the new product."""
        if 'history_log' not in self._fields:
            return

        try:
            now = datetime.now()
            formatted_date = now.strftime('%d/%m/%Y %H:%M:%S')

            original_name = original_data.get('name', 'Unknown')
            original_sku = original_data.get('default_code', '')
            sku_text = f" (SKU: {original_sku})" if original_sku else ""

            history_message = (
                f'<div style="border-left: 3px solid #6C757D; padding-left: 10px; '
                f'margin-bottom: 15px;"><small>Duplicated from '
                f'<strong>{original_name}</strong>{sku_text} on {formatted_date}</small></div>'
            )

            new_product = self.browse(new_product_id)
            new_product.with_context(
                skip_history_log=True,
                tracking_disable=True,
            ).write({'history_log': history_message})

        except Exception as e:
            _logger.warning("Failed to write history log for %s: %s", new_product_id, e)

    def _restore_product_images(self, new_product_id, backup_images):
        """Restore images to the new product."""
        if not backup_images:
            return

        try:
            ProductImage = self.env['product.image']
            existing_images = ProductImage.search([('product_tmpl_id', '=', new_product_id)])
            if existing_images:
                existing_images.unlink()

            for img_data in backup_images:
                ProductImage.create({
                    'product_tmpl_id': new_product_id,
                    'name': img_data.get('name', 'Image'),
                    'image_1920': img_data.get('image_1920'),
                    'is_primary': img_data.get('is_primary', False),
                    'sequence': img_data.get('sequence', 0),
                })

        except Exception as e:
            _logger.warning("Failed to restore images for %s: %s", new_product_id, e)

    def _create_variant_ids(self):
        if self.env.context.get("variant_creation"):
            return super(ProductTemplate, self)._create_variant_ids()
        return True

    def action_open_variant(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'variant_creation',
            'params': {
                'resModel': self._name,
                'resId': self.id,
                'name': self.name
            }
        }

class ProductMasterUnlinkWizard(models.TransientModel):
    _name = 'product.template.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Product master'

    product_id = fields.Many2one('product.template', string="Product Master", readonly=True)
    product_variant_id = fields.Many2one("product.product", string="Product Variant", readonly=True)

    def confirm_unlink(self):
        if self.product_variant_id:
            self.product_variant_id.unlink()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Products',
                'res_model': 'product.product',
                'view_mode': 'list',
                'view_id': self.env.ref('pim_ext.view_product_product_management_tree').id,
                'context': {'no_breadcrumbs': True},
            }
        if self.product_id:
            self.product_id.unlink()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Products',
                'res_model': 'product.template',
                'view_mode': 'list',
                'view_id': self.env.ref('pim_ext.view_product_management_tree').id,
                'context': {'no_breadcrumbs': True,
                            },
            }


class ProductImage(models.Model):
    _inherit = 'product.image'

    product_create_id = fields.Many2one(
        'product.create.master',
        string="Product Create",
        ondelete='cascade',
        index=True
    )
    image_url = fields.Char(string="Image URL")
    video_file = fields.Binary("Video File", attachment=True)
    video_filename = fields.Char("Video Filename")
    video_url = fields.Char("Video URL")
    bg_last_modified = fields.Datetime(
        string="BG Last Modified",
        readonly=True,
        copy=False
    )
    image_1920_original = fields.Binary(
        "Original Image Backup",
        attachment=True,
        copy=False,
        store=True,
        readonly=False
    )
    bg_removed = fields.Boolean(
        "Background Removed",
        default=False,
        copy=False,
        store=True,
        readonly=False
    )
    upload_method = fields.Selection([
        ('upload', 'Direct Upload'),
        ('url', 'URL'),
        ('drag_drop', 'Drag & Drop')
    ], string="Upload Method", default='upload')
    is_primary = fields.Boolean("Primary Image", default=False)
    file_type = fields.Selection([
        ('image', 'Image'),
        ('video', 'Video')
    ], string="Media Type", compute="_compute_file_info", store=True)
    file_size = fields.Float(
        string="File Size (MB)",
        compute="_compute_file_info",
        store=True
    )
    file_format = fields.Char(
        string="File Format",
        compute="_compute_file_info",
        store=True
    )

    @api.depends('image_1920', 'video_file', 'video_url', 'image_url', 'name', 'video_filename')
    def _compute_file_info(self):
        """Compute file type, format, and size for each media record"""
        for rec in self:
            if not rec.id or isinstance(rec.id, models.NewId):
                rec.file_type = 'image'
                rec.file_size = 0.0
                rec.file_format = 'UNKNOWN'
                continue

            # Determine media type
            rec.file_type = 'video' if (rec.video_file or rec.video_url) else 'image'

            # Determine file format from filename
            filename = rec.video_filename or rec.name or ''
            rec.file_format = filename.split('.')[-1].upper() if '.' in filename else 'UNKNOWN'

            # Calculate file size
            try:
                if rec.image_1920:
                    rec.file_size = len(base64.b64decode(rec.image_1920)) / (1024 * 1024)
                elif rec.video_file:
                    rec.file_size = len(base64.b64decode(rec.video_file)) / (1024 * 1024)
                else:
                    rec.file_size = 0.0
            except Exception:
                rec.file_size = 0.0

    @api.model
    def get_upload_constraints(self):
        """Return upload constraints for frontend validation"""
        return {
            'max_size_mb': 10.0,
            'allowed_image_formats': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'allowed_video_formats': ['video/mp4', 'video/webm', 'video/ogg'],
        }

    @api.model
    def create_from_urls(self, product_id, urls, model_name='product.template', is_variant=False):
        """
        Create product images from URLs with robust error handling

        Args:
            product_id (int): ID of the product
            urls (list): List of media URLs
            model_name (str): Model name (product.template, product.product, etc.)
            is_variant (bool): Whether this is for a variant

        Returns:
            dict: Results containing success IDs and errors
        """
        results = {'success': [], 'errors': []}

        for url in urls:
            url = url.strip()
            if not url:
                continue

            try:
                content = self.fetch_url_content(url)

                if not content['success']:
                    results['errors'].append({'url': url, 'error': content['error']})
                    continue

                vals = {
                    'name': url.split('/')[-1] or 'URL Media',
                    'upload_method': 'url',
                }

                # Set parent relationship
                if model_name == 'product.template' or not is_variant:
                    vals['product_tmpl_id'] = product_id
                elif model_name == 'product.product' or is_variant:
                    vals['product_variant_id'] = product_id
                elif model_name == 'product.create.master':
                    vals['product_create_id'] = product_id

                # Set media-specific fields
                if content.get('isVideo'):
                    vals['video_url'] = url
                    if content.get('data'):
                        vals['video_file'] = content['data']
                else:
                    vals['image_url'] = url
                    if content.get('data'):
                        vals['image_1920'] = content['data']

                rec = self.create(vals)
                results['success'].append(rec.id)

            except Exception as e:
                _logger.error(f"Error creating image from URL {url}: {str(e)}")
                results['errors'].append({'url': url, 'error': str(e)})

        return results

    @api.model
    def get_original_image_data(self, image_id):
        """
        Get original image data for restoration

        Args:
            image_id (int): ID of the product.image record

        Returns:
            dict: Original image data or error
        """
        try:
            image_record = self.browse(image_id)

            if not image_record.exists():
                return {'success': False, 'error': 'Image not found'}

            if not image_record.image_1920_original:
                return {'success': False, 'error': 'No original image found'}

            return {
                'success': True,
                'data': image_record.image_1920_original
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def remove_background(self, image_data):
        """
        Remove background from image using rembg library
        Optimized for low-memory servers (256px max dimension)

        Args:
            image_data (str): Base64 encoded image

        Returns:
            dict: Result with processed image or error
        """
        try:

            # Decode and optimize image
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
            input_image = ImageOps.exif_transpose(input_image)

            # Resize for memory optimization
            max_dimension = 256
            if max(input_image.size) > max_dimension:
                ratio = max_dimension / max(input_image.size)
                new_size = tuple(int(dim * ratio) for dim in input_image.size)
                input_image = input_image.resize(new_size, Image.LANCZOS)

            # Convert to RGB
            if input_image.mode != 'RGB':
                input_image = input_image.convert('RGB')

            # Configure ONNX Runtime for minimal memory usage
            session_options = ort.SessionOptions()
            session_options.intra_op_num_threads = 1
            session_options.inter_op_num_threads = 1
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            session_options.enable_mem_pattern = False
            session_options.enable_mem_reuse = True

            # Create rembg session
            session = new_session("u2netp", providers=['CPUExecutionProvider'])

            # Remove background
            output_image = remove(
                input_image,
                session=session,
                alpha_matting=False,
                post_process_mask=False,
                only_mask=False
            )

            # Cleanup
            del session
            del input_image
            import gc
            gc.collect()

            # Save as optimized PNG
            output_buffer = io.BytesIO()
            output_image.save(output_buffer, format='PNG', optimize=True, compress_level=9)
            output_buffer.seek(0)

            output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')

            return {
                'success': True,
                'data': output_base64,
                'format': 'PNG'
            }

        except Exception as e:
            error_msg = str(e)
            if 'Failed to allocate memory' in error_msg or 'RUNTIME_EXCEPTION' in error_msg:
                return {
                    'success': False,
                    'error': 'Insufficient server memory. Try: 1) Smaller image, 2) Restart Odoo, 3) Use remove.bg API'
                }
            _logger.error(f"Background removal error: {error_msg}")
            return {
                'success': False,
                'error': f"Processing failed: {error_msg[:100]}"
            }

    @api.model
    def get_image_data(self, image_id):
        """
        Get base64 image data for a product image

        Args:
            image_id (int): ID of the product.image record

        Returns:
            dict: Image data or error
        """
        try:
            image_record = self.browse(image_id)

            if not image_record.exists():
                return {
                    'success': False,
                    'error': 'Image not found'
                }

            return {
                'success': True,
                'data': image_record.image_1920
            }

        except Exception as e:
            _logger.error(f"Error getting image data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _clear_other_primaries(self, vals):
        """
        Helper method to ensure only one primary image per product

        Args:
            vals (dict): Values being written/created
        """
        if not vals.get('is_primary'):
            return

        for record in self:
            # Determine parent relationship
            parent_field = False
            parent_id = False

            if vals.get('product_tmpl_id') or record.product_tmpl_id:
                parent_field, parent_id = 'product_tmpl_id', vals.get('product_tmpl_id') or record.product_tmpl_id.id
            elif vals.get('product_variant_id') or record.product_variant_id:
                parent_field, parent_id = 'product_variant_id', vals.get(
                    'product_variant_id') or record.product_variant_id.id
            elif vals.get('product_create_id') or record.product_create_id:
                parent_field, parent_id = 'product_create_id', vals.get(
                    'product_create_id') or record.product_create_id.id

            if parent_field and parent_id:
                # Unset primary flag for all other images
                domain = [(parent_field, '=', parent_id), ('is_primary', '=', True), ('id', '!=', record.id or 0)]
                others = self.search(domain)
                if others:
                    super(ProductImage, others).write({'is_primary': False})

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure names and handle primary logic"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = vals.get('video_filename') or f"Media {fields.Datetime.now()}"

        records = super().create(vals_list)

        for record in records:
            if record.is_primary:
                record._clear_other_primaries({'is_primary': True})

        return records

    def write(self, vals):
        """Override write to handle primary logic"""
        res = super().write(vals)
        if vals.get('is_primary'):
            self._clear_other_primaries(vals)
        return res

    @api.model
    def fetch_url_content(self, url):
        """
        Fetch content from URL with YouTube/Vimeo detection

        Args:
            url (str): URL to fetch

        Returns:
            dict: Content data or error
        """
        try:
            # Validate URL
            if not url or not url.startswith(('http://', 'https://')):
                return {'success': False, 'error': 'Invalid URL format'}

            # Detect YouTube/Vimeo (no download needed)
            youtube_pattern = r'(youtube\.com|youtu\.be)'
            vimeo_pattern = r'(vimeo\.com)'

            if re.search(youtube_pattern, url) or re.search(vimeo_pattern, url):
                return {
                    'success': True,
                    'isImage': False,
                    'isVideo': True,
                    'contentType': 'video/embed',
                    'data': None,
                    'size': 0
                }

            # Download content
            response = requests.get(url, timeout=10, stream=True, allow_redirects=True)

            if response.status_code != 200:
                return {'success': False, 'error': f'HTTP {response.status_code}'}

            # Parse content type
            content_type = response.headers.get('content-type', '').lower()
            if ',' in content_type:
                content_type = content_type.split(',')[0].strip()
            if ';' in content_type:
                content_type = content_type.split(';')[0].strip()

            is_video = content_type.startswith('video/')
            is_image = content_type.startswith('image/')

            if not is_video and not is_image:
                return {'success': False, 'error': f'Invalid content type: {content_type}'}

            # Check file size limit (10MB)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:
                return {'success': False, 'error': 'File size exceeds 10MB limit'}

            content = response.content
            if len(content) > 10 * 1024 * 1024:
                return {'success': False, 'error': 'File size exceeds 10MB limit'}

            # Validate format
            if is_image:
                allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if content_type not in allowed:
                    return {'success': False, 'error': f'Unsupported image format: {content_type}'}
            elif is_video:
                allowed = ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime']
                if content_type not in allowed:
                    return {'success': False, 'error': f'Unsupported video format: {content_type}'}

            # Encode to base64
            base64_data = base64.b64encode(content).decode('utf-8')

            return {
                'success': True,
                'data': base64_data,
                'isVideo': is_video,
                'isImage': is_image,
                'contentType': content_type,
                'size': len(content)
            }

        except Exception as e:
            _logger.error(f"Error fetching URL {url}: {str(e)}")
            return {'success': False, 'error': f'Request failed: {str(e)}'}


class ProductMediaUploadWizard(models.TransientModel):
    _name = 'product.media.upload.wizard'
    _description = 'Product Media Upload Wizard'

    product_tmpl_id = fields.Many2one('product.template', string='Product', required=True)
    product_variant_id = fields.Many2one('product.product', string='Product Variant')
    upload_type = fields.Selection([
        ('url', 'Upload from URLs'),
        ('file', 'Upload Files'),
    ], string='Upload Method', default='url', required=True)
    media_urls = fields.Text(
        string='Media URLs',
        help='Enter one URL per line. Supports images (JPG, PNG, WEBP) and videos (YouTube, Vimeo, MP4).'
    )
    media_files_ids = fields.One2many('product.media.file.line', 'wizard_id', string='Media Files')

    def action_upload_media(self):
        """Process media upload based on selected method"""
        self.ensure_one()

        result_notification = {}

        if self.upload_type == 'url':
            result_notification = self._upload_from_urls()
        else:
            result_notification = self._upload_from_files()

        return {
            'type': 'ir.actions.act_window_close',
            'infos': result_notification
        }

    def _upload_from_urls(self):
        """Upload media from URLs"""
        if not self.media_urls:
            raise ValidationError(_('Please enter at least one URL'))

        urls = [url.strip() for url in self.media_urls.split('\n') if url.strip()]

        if not urls:
            raise ValidationError(_('No valid URLs found'))

        target_id = self.product_variant_id.id if self.product_variant_id else self.product_tmpl_id.id
        is_variant = bool(self.product_variant_id)

        results = self.env['product.image'].create_from_urls(target_id, urls, is_variant=is_variant)

        return self._format_notification(results['success'], results['errors'])

    def _upload_from_files(self):
        """Upload media from file attachments"""
        if not self.media_files_ids:
            raise ValidationError(_('Please add at least one file'))

        success_count = 0
        errors = []

        for file_line in self.media_files_ids:
            try:
                mimetype, _ = mimetypes.guess_type(file_line.filename)
                if not mimetype:
                    ext = file_line.filename.split('.')[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                        mimetype = 'image/jpeg'
                    elif ext in ['mp4', 'webm', 'ogg']:
                        mimetype = 'video/mp4'

                vals = {
                    'name': file_line.filename,
                    'upload_method': 'upload',
                    'is_primary': file_line.is_primary
                }

                if mimetype and mimetype.startswith('image'):
                    vals['image_1920'] = file_line.file_data
                elif mimetype and mimetype.startswith('video'):
                    vals['video_file'] = file_line.file_data
                    vals['video_filename'] = file_line.filename
                else:
                    errors.append(f"{file_line.filename}: Unsupported file type")
                    continue

                if self.product_variant_id:
                    vals['product_variant_id'] = self.product_variant_id.id
                    vals['product_tmpl_id'] = self.product_variant_id.product_tmpl_id.id
                else:
                    vals['product_tmpl_id'] = self.product_tmpl_id.id

                if file_line.is_primary:
                    domain = [('product_tmpl_id', '=', vals['product_tmpl_id'])]
                    if self.product_variant_id:
                        domain.append(('product_variant_id', '=', self.product_variant_id.id))
                    self.env['product.image'].search(domain).write({'is_primary': False})

                self.env['product.image'].create(vals)
                success_count += 1

            except Exception as e:
                _logger.error(f"File upload error: {str(e)}")
                errors.append(f"{file_line.filename}: {str(e)}")

        return self._format_notification(range(success_count), [{'url': 'file', 'error': e} for e in errors])

    def _format_notification(self, success_list, error_list):
        """Format UI notification message"""
        success_count = len(success_list)
        error_count = len(error_list)

        message = f"Uploaded: {success_count} media file(s)."
        if error_count > 0:
            message += f"\nFailed: {error_count}."

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upload Results'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'}
            }
        }


class ProductMediaFileLine(models.TransientModel):
    _name = 'product.media.file.line'
    _description = 'Media File Line for Upload'

    wizard_id = fields.Many2one(
        'product.media.upload.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    filename = fields.Char(string='Filename', required=True)
    file_data = fields.Binary(string='File', required=True, attachment=False)
    is_primary = fields.Boolean(string='Set as Primary')
