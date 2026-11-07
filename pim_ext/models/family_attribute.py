# -*- coding: utf-8 -*-

import time, pytz
import re
import json

from datetime import datetime, timedelta, timezone, date
from email.policy import default
from markupsafe import Markup
import pytz

import random
from lxml import etree
from odoo import models, api, fields, _, tools
from odoo.exceptions import UserError, ValidationError
import traceback, pdb, inspect

from odoo.tools import drop_view_if_exists
import logging

_logger = logging.getLogger(__name__)


class FamilyAttribute(models.Model):
    _name = 'family.attribute'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Family'

    code = fields.Char(string="Code", readonly=True)
    description = fields.Text(string="Description")

    name = fields.Char('Name', required=True, tracking=True)
    supplier_id = fields.Many2one('res.partner', 'Supplier')
    brand_id = fields.Many2one('brand.attribute', 'Brand')
    manufacture_id = fields.Many2one('manufacturer.attribute', 'Manufacturer')
    attributes_group_ids = fields.Many2many('attribute.group', string='Attributes Groups', tracking=True,
                                            domain=[('active', '=', True)])
    taxonomy_ids = fields.Many2many('product.public.category', string="Taxonomy")
    attch_ids = fields.Many2many('ir.attachment', 'ir_attach_rel', 'record_relation_id', 'attachment_id',
                                 string="Attachments")
    complementary_categ_ids = fields.Many2many('product.public.category', 'custom_categ_rel', 'family_id', 'cteg_id',
                                               string="Complementary Categories")
    product_family_ids = fields.One2many('family.products', 'family_id', 'Products')
    product_image = fields.Image(string="Image", copy=False, attachment=True, max_width=1024, max_height=1024)
    buyer_id = fields.Many2one('res.partner', 'Buyer')
    availability = fields.Selection([('all', 'All Channel')], 'Availability')
    swatch = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Swatch')
    gift = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Gift')
    # attribute1_id = fields.Many2one('product.attribute1', 'Attribute 1')
    # attribute2_id = fields.Many2one('product.attribute2', 'Attribute 2')
    # attribute3_id = fields.Many2one('product.attribute3', 'Attribute 3')
    # attribute4_id = fields.Many2one('product.attribute4', 'Attribute 4')
    exist_attribute_ids = fields.Many2many('product.attribute', 'family_mapped_attributes_rel', 'family_id',
                                           'attribute_id', string='Exist Attributes')
    exist_group_ids = fields.Many2many('attribute.group', 'family_mapped_groups_rel', 'family_id', 'attribute_group_id',
                                       string='Exist Attribute Groups')
    asn_description = fields.Html('ASN Description')
    product_families_ids = fields.One2many('family.products.line', 'families_id', 'Attributes', readonly=False)
    family_attribute_ids = fields.One2many('family.attributes', 'family_id', 'Family Attributes', readonly=False)
    variant_line_ids = fields.One2many('family.variant.line', 'variant_family_id', 'Variants', readonly=False)

    attribute_label = fields.Char(string='Translation')

    parent_id = fields.Many2one(
        'family.attribute',
        string='Parent Group',
        ondelete='cascade',
    )
    family_ids = fields.One2many(
        'family.attribute',
        'parent_id',
        compute='_compute_family_ids',
        string='Sub-groups'
    )

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

    is_create_mode = fields.Boolean(default=False, string='Create Mode')

    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    family_sequence_id = fields.Many2one('family.attribute.sequence', readonly=True)

    def _log_changes(self, rec, vals, action):
        # Get the current time in UTC and convert to user's timezone
        updated_write_date_utc = fields.Datetime.now()
        user_tz = self.env.user.tz or 'UTC'
        updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
        user_name = self.env.user.display_name
        changes = []

        # Fields to track
        tracked_fields = ['name', 'description', 'supplier_id', 'brand_id', 'manufacture_id', 'availability',
                          'swatch', 'gift']
        tracked_one2many_fields = {
            'product_families_ids': ['attribute_id', 'attribute_group_id', 'completeness_percent'],
            'variant_line_ids': ['name', 'variant_ids'],
            'family_attribute_ids': ['attribute_id', 'attribute_group_id'],
        }

        # Track direct field changes
        for key in vals:
            if key in tracked_fields:
                field_label = rec._fields[key].string
                old_value = getattr(rec, key, 'N/A') if action == "update" else 'N/A'
                new_value = vals[key] if vals[key] is not None else 'N/A'

                if isinstance(rec._fields[key], fields.Many2one):
                    old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                    new_value = self.env[rec._fields[key].comodel_name].browse(
                        new_value).display_name if new_value != 'N/A' else 'N/A'

                change_entry = f"""
                  <li>
                      <strong>{field_label}</strong><br>
                      <span style='color: red;'>Old value:</span> {old_value}  
                           
                      <span style='color: green;'>New value:</span> {new_value}
                  </li>
                  """
                changes.append(change_entry)

        # Track One2many field changes
        for field, subfields in tracked_one2many_fields.items():
            if field in vals:
                field_label = rec._fields[field].string
                for command in vals[field]:
                    if command[0] == 1:  # Update existing record
                        line_id = rec[field].browse(command[1])
                        for subfield in subfields:
                            if subfield in command[2]:
                                subfield_label = line_id._fields[subfield].string
                                old_value = getattr(line_id, subfield, 'N/A')
                                new_value = command[2][subfield] if command[2][subfield] is not None else 'N/A'

                                if isinstance(line_id._fields[subfield], fields.Many2one):
                                    old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                                    new_value = self.env[line_id._fields[subfield].comodel_name].browse(
                                        new_value).display_name if new_value != 'N/A' else 'N/A'
                                elif isinstance(line_id._fields[subfield], fields.Many2many):
                                    old_value = ', '.join(
                                        old_value.mapped('display_name')) if old_value else 'N/A'
                                    if isinstance(new_value, (list, tuple)):
                                        ids = [cmd[1] if isinstance(cmd, tuple) and cmd[0] in (1, 4) else cmd
                                               for cmd in new_value if isinstance(cmd, (int, tuple))]
                                        new_value = ', '.join(
                                            self.env[line_id._fields[subfield].comodel_name].browse(
                                                ids).mapped('display_name')) if ids else 'N/A'
                                    else:
                                        new_value = new_value if new_value is not None else 'N/A'

                                change_entry = f"""
                                  <li>
                                      <strong>{subfield_label} (in {field_label})</strong><br>
                                      <span style='color: red;'>Old value:</span> {old_value}  
                                           
                                      <span style='color: green;'>New value:</span> {new_value}
                                  </li>
                                  """
                                changes.append(change_entry)

                    elif command[0] == 0:  # New record added
                        new_vals = command[2]
                        for subfield in subfields:
                            subfield_label = self.env[rec._fields[field].comodel_name]._fields[subfield].string
                            new_value = new_vals.get(subfield, 'N/A') if subfield in new_vals else 'N/A'
                            old_value = 'N/A'  # New records have no old value

                            if isinstance(self.env[rec._fields[field].comodel_name]._fields[subfield],
                                          fields.Many2one):
                                new_value = self.env[self.env[rec._fields[field].comodel_name]._fields[
                                    subfield].comodel_name].browse(
                                    new_value).display_name if new_value != 'N/A' else 'N/A'
                            elif isinstance(self.env[rec._fields[field].comodel_name]._fields[subfield],
                                            fields.Many2many):
                                if isinstance(new_value, (list, tuple)):
                                    ids = [cmd[1] if isinstance(cmd, tuple) and cmd[0] in (1, 4) else cmd for
                                           cmd in new_value if isinstance(cmd, (int, tuple))]
                                    new_value = ', '.join(self.env[self.env[
                                        rec._fields[field].comodel_name]._fields[
                                        subfield].comodel_name].browse(ids).mapped(
                                        'display_name')) if ids else 'N/A'
                                else:
                                    new_value = new_value if new_value is not None else 'N/A'

                            change_entry = f"""
                              <li>
                                  <strong>{subfield_label} (in New {field_label})</strong><br>
                                  <span style='color: red;'>Old value:</span> {old_value}  
                                       
                                  <span style='color: green;'>New value:</span> {new_value}
                              </li>
                              """
                            changes.append(change_entry)

                    elif command[0] == 2:  # Deletion
                        removed_record = rec[field].browse(command[1])
                        if removed_record.exists():
                            for subfield in subfields:
                                subfield_label = removed_record._fields[subfield].string
                                old_value = getattr(removed_record, subfield, 'N/A')
                                new_value = 'N/A'  # Removed records have no new value

                                if isinstance(removed_record._fields[subfield], fields.Many2one):
                                    old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                                elif isinstance(removed_record._fields[subfield], fields.Many2many):
                                    old_value = ', '.join(
                                        old_value.mapped('display_name')) if old_value else 'N/A'

                                change_entry = f"""
                                  <li>
                                      <strong>{subfield_label} (in Removed {field_label})</strong><br>
                                      <span style='color: red;'>Old value:</span> {old_value}  
                                           
                                      <span style='color: green;'>New value:</span> {new_value}
                                  </li>
                                  """
                                changes.append(change_entry)

        if changes:
            action_text = "Created by" if action == "create" else "Updated by"
            header = f"<small>{action_text} {user_name} on {updated_write_date}</small>"
            full_message = f"""
              <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                  {header}
                  <ul style="list-style-type: none; padding-left: 0;">
                      {''.join(changes)}
                  </ul>
              </div>
              """
            rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')

    def write(self, vals):
        res = super(FamilyAttribute, self).write(vals)

        for rec in self:
            rec._log_changes(rec, vals, action="update")

            # --- Sync sequence lines if exist_group_ids changed ---
            if 'exist_group_ids' in vals and rec.family_sequence_id:
                new_groups = rec.exist_group_ids
                existing_lines = rec.family_sequence_id.attr_group_ids.mapped("attribute_group_id")
                # Groups to add
                groups_to_add = new_groups - existing_lines
                for grp in groups_to_add:
                    self.env['family.attribute.seq.line'].create({
                        'family_sequence_id': rec.family_sequence_id.id,
                        'attribute_group_id': grp.id,
                    })

                # Groups to remove
                groups_to_remove = existing_lines - new_groups
                lines_to_remove = rec.family_sequence_id.attr_group_ids.filtered(
                    lambda l: l.attribute_group_id in groups_to_remove
                )
                lines_to_remove.unlink()

            # --- Sequence creation/update logic ---
            if rec.family_attribute_ids and not rec.family_sequence_id:
                rec.update_sequence_views()
            elif rec.family_attribute_ids and rec.family_sequence_id:
                rec.update_view_in_sequence()

            # --- Sync exist attributes if not already syncing ---
            if not self.env.context.get('syncing_exist_attrs'):
                rec.with_context(syncing_exist_attrs=True).sync_exist_attribute_ids()

        return res

    def update_attribute_group_views(self):
        for rec in self:
            company_name = rec.company_id.name
            company_id = rec.company_id.id
            attributes = rec.mapped('family_attribute_ids').mapped('attribute_id')
            attribute_lines = rec.family_attribute_ids

            attribute_groups = {}
            for line in attribute_lines:
                group_name = line.attribute_group_id.name or "default"
                attribute = line.attribute_id

                if group_name in attribute_groups:
                    attribute_groups[group_name].append(attribute)
                else:
                    attribute_groups[group_name] = [attribute]
            for group_name, group_attributes in attribute_groups.items():
                safe_group_id = group_name.lower().replace(' ', '_').replace('&', 'and')
                group_view_name = 'product_attribute_' + company_name.lower().replace(' ', '_') + '_' + safe_group_id
                group_exist = self.env['ir.ui.view'].search([
                    ('name', 'ilike', group_view_name),
                    ('active', 'in', [True, False])
                ], limit=1)
                if not group_exist:
                    continue

                if group_exist.arch_base:
                    grp_arch_tree = etree.fromstring(group_exist.arch_base)
                    updated = False
                    group_node = grp_arch_tree.find(f".//group[@id='{safe_group_id}']")
                    if group_node is not None:
                        group_invisible = group_node.get("invisible")
                        new_id = str(rec.id)
                        if group_invisible and group_invisible.strip().lower() != 'false':
                            match = re.search(r'\[(.*?)\]', group_invisible)
                            if match:
                                id_list = [x.strip() for x in match.group(1).split(',') if x.strip()]
                                if new_id not in id_list:
                                    id_list.append(new_id)
                                    group_node.set("invisible", f"family_id not in [{', '.join(id_list)}]")
                                    updated = True
                            else:
                                group_node.set("invisible", f"family_id not in [{new_id}]")
                                updated = True
                        else:
                            group_node.set("invisible", f"family_id not in [{new_id}]")
                            updated = True
                    # Show fields that are in default_attrs_val
                    for a in group_attributes:
                        # attributes_list.append(a.original_name)
                        xpath_expr = f".//field[@name='{a.original_name}']"
                        field_node = grp_arch_tree.find(xpath_expr)
                        if field_node is not None:
                            column_invisible = field_node.get("invisible")
                            new_id = str(rec.id)
                            if column_invisible and column_invisible.strip().lower() != 'false':
                                match = re.search(r'\[(.*?)\]', column_invisible)
                                if match:
                                    id_list = [x.strip() for x in match.group(1).split(',') if x.strip()]
                                    if new_id not in id_list:
                                        id_list.append(new_id)
                                    field_node.set("invisible", f"family_id not in [{', '.join(id_list)}]")
                                    updated = True
                                else:
                                    # If column_invisible is set but not in expected format, override it
                                    field_node.set("invisible", f"family_id not in [{new_id}]")
                                    updated = True
                            else:
                                # If column_invisible is 'False' or not set at all
                                field_node.set("invisible", f"family_id not in [{new_id}]")
                                updated = True
                    if updated:
                        updated_arch = etree.tostring(grp_arch_tree, pretty_print=True).decode()
                        group_exist.write({'arch_base': updated_arch})

    def remove_attribute_family_in_view(self, attribute, group):
        for rec in self:
            company_name = rec.company_id.name
            safe_group_id = group.name.lower().replace(' ', '_').replace('&', 'and')
            group_view_name = f'product_attribute_{company_name.lower().replace(" ", "_")}_{safe_group_id}'

            view = self.env['ir.ui.view'].search([
                ('name', 'ilike', group_view_name),
                ('active', 'in', [True, False])
            ], limit=1)

            if not view or not view.arch_base:
                continue

            grp_arch_tree = etree.fromstring(view.arch_base)
            updated = False
            fam_id_str = str(rec.id)

            # check if other attributes in this group are still linked to this family
            other_attrs = self.env['family.attributes'].search([
                ('family_id', '=', rec.id),
                ('attribute_group_id', '=', group.id),
                ('attribute_id', '!=', attribute.id)
            ])
            has_other_attrs = bool(other_attrs)

            # update <group> invisible ONLY if no other attrs left for this family
            if not has_other_attrs:
                group_node = grp_arch_tree.find(f".//group[@id='{safe_group_id}']")
                if group_node is not None:
                    inv = group_node.get("invisible")
                    if inv:
                        match = re.search(r'\[(.*?)\]', inv)
                        if match:
                            id_list = [x.strip() for x in match.group(1).split(',') if x.strip()]
                            if fam_id_str in id_list:
                                id_list.remove(fam_id_str)
                                if id_list:
                                    group_node.set("invisible", f"family_id not in [{', '.join(id_list)}]")
                                else:
                                    group_node.set("invisible", "1")
                                updated = True

            # Always update the specific field invisible
            xpath_expr = f".//field[@name='{attribute.original_name}']"
            field_node = grp_arch_tree.find(xpath_expr)
            if field_node is not None:
                inv = field_node.get("invisible")
                if inv:
                    match = re.search(r'\[(.*?)\]', inv)
                    if match:
                        id_list = [x.strip() for x in match.group(1).split(',') if x.strip()]
                        if fam_id_str in id_list:
                            id_list.remove(fam_id_str)
                            if id_list:
                                field_node.set("invisible", f"family_id not in [{', '.join(id_list)}]")
                            else:
                                field_node.set("invisible", "1")
                            updated = True

            # save if modified
            if updated:
                new_arch = etree.tostring(grp_arch_tree, pretty_print=True).decode()
                view.write({'arch_base': new_arch})

    def _compute_family_ids(self):
        for record in self:
            record.family_ids = self.env['family.attribute'].search([('company_id', '=', self.env.company.id)])

    def attribute_family_open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Family',
            'res_model': 'family.attribute',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_split_family_view_custom').id,
            'context': {'no_breadcrumbs': True,
                        'default_is_create_mode': False,
                        },
            'res_id': self.id,
        }

    # delete Family
    def attribute_family_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'attribute.family.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_family_id': self.id},
        }

    def save_family(self):
        # self.update_attribute_group_views()
        if self.family_attribute_ids and not self.family_sequence_id:
            self.update_sequence_views()
        elif self.family_attribute_ids and self.family_sequence_id:
            self.update_view_in_sequence()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'family.attribute',
            'view_id': self.env.ref('pim_ext.view_split_family_view_custom').id,
            'res_id': self.id,
            'context': {'no_breadcrumbs': True},
            'target': 'current',
        }

    def action_back_to_menu(self):
        menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Families')])
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record.code = self.env['ir.sequence'].next_by_code('family.attribute') or None

            if record.family_attribute_ids:
                record.sync_exist_attribute_ids()

            record._log_changes(record, vals, action="create")

            if record.family_attribute_ids and not record.family_sequence_id:
                record.update_sequence_views()
            elif record.family_attribute_ids and record.family_sequence_id:
                record.update_view_in_sequence()

        return records

    def sync_exist_attribute_ids(self):
        for rec in self:
            attributes = []
            groups = []
            for line in rec.family_attribute_ids:
                if line.attribute_id:
                    attributes.append(line.attribute_id.id)
                if line.attribute_group_id:
                    groups.append(line.attribute_group_id.id)

            # Use `with_context` to avoid re-triggering `write()` logic
            rec.with_context(syncing_exist_attrs=True).write({
                'exist_attribute_ids': [(6, 0, attributes)],
                'exist_group_ids': [(6, 0, groups)]
            })

    def edit_family(self):
        pass

    def delete_family(self):

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'delete.family.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_current_family_id': self.id,
                'default_current_family': self._origin.id,
            },
        }

    def action_update(self):
        attribute_group = self.env['attribute.group'].search([("attribute_family_id", "in", self.id)])
        for record in attribute_group:
            self.attributes_group_ids = [(4, record.id)]

    def mass_edit(self):
        res = []
        return res

    def create_pim_attribute_family(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Family',
            'res_model': 'family.attribute',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_split_family_view_custom').id,
            'target': 'current',
            'context': {
                'default_family_ids': self.env['family.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
                'default_is_create_mode': True,
            },
        }
        # return {
        #      'name':_('Create Family'),
        #      'type':'ir.actions.act_window',
        #      'view_mode':'form',
        #      'res_model':'family.attribute',
        # }

    def action_open_attribute_group_wizard(self):
        return {
            'name': _("Add Attribute Group"),
            'type': 'ir.actions.act_window',
            'res_model': 'attribute.group.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attribute_family_id': self.id},
        }

    def action_open_add_attribute_wizard(self):
        return {
            'name': _("Add Attribute"),
            'type': 'ir.actions.act_window',
            'res_model': 'add.attribute.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attribute_family_id': self.id},
        }

    def action__add_variant_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'attribute.variant.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attribute_family_id': self.id},
        }

    def action_open_attribute_sequence_wizard(self):
        record = self.env['family.attribute.sequence'].sudo().search([('family_id', '=', self.id)], limit=1,
                                                                     order="id desc")
        if record:
            res_id = record.id
        else:
            res_id = False
        return {
            'name': (_("Family Attribute Group Sequence")),
            'type': 'ir.actions.act_window',
            'res_model': 'family.attribute.sequence',
            'view_mode': 'form',
            'res_id': res_id,
            'target': 'new',
            'context': {'default_family_id': self.id},
        }

    def update_view_in_sequence(self, lang=None):
        widgets_mapping = {
            'image': 'image',
            'multi_select': 'many2many_tags',
            'price': 'monetary',
            'color': 'pim_color',
            'date': 'date',
        }

        for rec in self:
            company_name = rec.company_id.name.lower().replace(' ', '_')
            family_name = rec.name.lower().replace(' ', '_')
            view_name = f'product_attribute_{company_name}_{family_name}'
            # Create a full <form> wrapper with a notebook
            form_root = etree.Element("form", {"string": "Product"})
            sheet_node = etree.SubElement(form_root, "sheet")
            notebook_node = etree.SubElement(sheet_node, "notebook")
            page_node = etree.SubElement(notebook_node, "page", {"id": "attributes_page", "string": "Attributes"})
            count = 0

            for line in rec.family_sequence_id.attr_group_ids.sorted(key=lambda l: l.sequence):
                count += 1
                grp = line.attribute_group_id
                safe_group_id = grp.name.lower().replace(' ', '_').replace('&', 'and')
                # add randon string to avoid duplicate id issue
                safe_group_id += '_' + str(random.randint(1000, 9999))

                div_col = etree.SubElement(page_node, "div",
                                           {"class": "g-col-sm-2", "invisible": f"family_id not in [{rec.id}]", })
                link = etree.SubElement(div_col, "div", {
                    "data-bs-toggle": "collapse",
                    "data-bs-target": "#" + safe_group_id,
                    "role": "button",
                    "aria-expanded": "true" if count == 1 else "false",
                    "aria-controls": safe_group_id,
                })
                header_div = etree.SubElement(link, "div", {
                    "class": "o_horizontal_separator mt-4 mb-3 text-uppercase fw-bolder small"
                })
                header_div.text = grp.name

                collapse = etree.SubElement(
                    page_node,
                    "div",
                    {
                        "class": "collapse show" if count == 1 else "collapse",
                        "id": safe_group_id,
                        "invisible": f"family_id not in [{rec.id}]",
                    }
                )
                # Create <group> block
                group_node = etree.SubElement(
                    collapse,
                    "group",
                    {
                        "id": safe_group_id,
                        "name": safe_group_id,
                        "collapsible": "1",
                        "expanded": "1",
                        "invisible": f"family_id not in [{rec.id}]",
                    }
                )
                # Collect attributes from family_attribute_ids linked to this group
                attributes = rec.family_attribute_ids.filtered(lambda l: l.attribute_group_id.id == grp.id)
                for attr_line in attributes:
                    attr = attr_line.attribute_id
                    widget = widgets_mapping.get(attr.display_type)
                    if not attr or not attr.original_name:
                        continue
                    # ---- Apply your field conditions ----
                    if attr.original_name and attr.display_type not in ['table', 'measurement']:
                        field_tag = f'''<field name="{attr.original_name}"'''
                        family_list = rec  # if you want multiple families, adapt this line
                        if family_list:
                            field_tag += f''' invisible="family_id not in {[rec.id]}"'''
                        else:
                            field_tag += f''' invisible="1"'''

                        # Handle widget
                        if widget:
                            field_tag += f''' widget="{widget}"'''

                        # Mandatory
                        if attr.is_mandatory:
                            field_tag += f''' required="0"'''

                        # Select typesdef update_view
                        if attr.display_type in ['simple_select', 'multi_select']:
                            options_dict = {"no_create_edit": True, "no_edit": True, "no_open": True}
                            safe_options = json.dumps(
                                options_dict)
                            field_tag += f''' options='{safe_options}' '''

                        if attr.display_type in ['file']:
                            field_tag += f''' filename='{attr.original_name}_file_name' '''
                        field_tag += f'''/>\n'''

                        # Append to group node as raw string
                        group_node.append(etree.XML(field_tag))
                    if attr.original_name and attr.display_type in ['file']:
                        field_tag = f'''<field name="{attr.original_name}_file_name" invisible="1"/>'''
                        group_node.append(etree.XML(field_tag))
                    if attr.original_name and attr.display_type in ['measurement']:
                        value_field = attr.original_name
                        uom_field = f"{attr.original_name}_mes"
                        if attr.multi_field_per_value == 'yes':
                            for index, rec in enumerate(attr.value_ids, start=1):
                                field_name = f"{attr.original_name}_mes_{index}"
                                block = f"""
                                    <div class="o_group overflow-auto">
                                        <div class="mb-1">
                                            <label for="{field_name}" class="o_form_label"/>
                                        </div>
                                        <div class="d-flex align-items-center">
                                            <field name="{field_name}" class="oe_inline" placeholder="00.0"/>
                                            <span class="mx-2">per</span>
                                            <field name="{uom_field}" class="oe_inline" 
                                                   options="{{'no_create': True, 'no_open': True}}" 
                                                   nolabel="1" style="flex: 0 0 auto; min-width: 40px;"/>
                                        </div>
                                    </div>
                                """
                                group_node.append(etree.XML(block))
                        else:
                            measurement_block = f"""
                                <div class="o_group overflow-auto">
                                    <div class="mb-1" name="{value_field}_row">
                                        <label for="{value_field}" class="o_form_label"/>
                                    </div>
                                    <div class="d-flex align-items-center">
                                        <field name="{value_field}" class="oe_inline" placeholder="00.0"/>
                                        <span class="mx-2">per</span>
                                        <field name="{uom_field}" class="oe_inline" 
                                               options="{{'no_create': True, 'no_open': True}}" 
                                               nolabel="1" style="flex: 0 0 auto; min-width: 40px;"/>
                                    </div>
                                </div>
                            """
                            group_node.append(etree.XML(measurement_block))
                            # block_val.append(field_val)
                            # measurement_block = f"""
                            #         <div class='row' name="{attr.original_name}_multi_block">
                            #             {''.join(block_val)}
                            #         </div>
                            #     """

                # Convert to final arch
            final_arch = etree.tostring(page_node, pretty_print=True).decode()
            default_view_id = self.env.ref('pim_ext.view_product_creation_split_view_custom').id
            product_product_view = self.env.ref('pim_ext.view_product_product_creation_split_view_custom').id
            # Create/Update View
            view = self.env['ir.ui.view'].search([('name', '=', view_name), ('model', '=', 'product.template')],
                                                 limit=1)
            product_view_ex = self.env['ir.ui.view'].search(
                [('name', '=', view_name), ('model', '=', 'product.product')],
                limit=1)
            if product_view_ex:
                product_view_ex.write({'arch_base': final_arch})
            else:
                self.env['ir.ui.view'].create({
                    'name': view_name,
                    'type': 'form',
                    'model': 'product.product',
                    'arch_base': final_arch,
                    'inherit_id': product_product_view,
                    'active': True,
                })
            if view:
                view.write({'arch_base': final_arch})
            else:
                self.env['ir.ui.view'].create({
                    'name': view_name,
                    'type': 'form',
                    'model': 'product.template',
                    'arch_base': final_arch,
                    'inherit_id': default_view_id,
                    'active': True,
                })

    def update_sequence_views(self, lang=None):
        active_ids = self.env.context.get('active_ids', [])
        families = self or self.env['family.attribute'].sudo().search(
            [('id', 'in', active_ids)], order="id asc")
        for rec in families:
            if rec.exist_group_ids:
                groups = self.env['attribute.group'].search([("id", 'in', rec.exist_group_ids.ids)])
                lines = [{
                    'attribute_group_id': grp.id,
                } for grp in groups]
                res_id = self.env['family.attribute.sequence'].sudo().create({
                    'family_id': rec.id,
                    'attr_group_ids': [(0, 0, group) for group in lines],
                })
                rec.update_view_in_sequence(lang=lang)


class AttributeFamilyUnlinkWizard(models.TransientModel):
    _name = 'attribute.family.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of family'

    family_id = fields.Many2one('family.attribute', string="Family")

    def confirm_unlink(self):
        menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Families')])
        if self.family_id:
            self.family_id.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }


class FamilyAttributes(models.Model):
    _name = 'family.attributes'
    _description = 'Family Attributes'

    family_id = fields.Many2one('family.attribute', 'Family', ondelete='cascade')
    attribute_id = fields.Many2one('product.attribute', string='Attribute', ondelete='cascade')
    attribute_company_id = fields.Many2one(related='attribute_id.company_id')
    attribute_group_id = fields.Many2one('attribute.group', string='Attribute Group')

    def unlink(self):
        """
        Enhanced unlink to properly remove attributes from family views
        and clean up empty groups.
        """
        families_to_update = {}

        for line in self:
            family = line.family_id
            if family.id not in families_to_update:
                families_to_update[family.id] = {
                    'family': family,
                    'attributes': [],
                    'groups': set()
                }

            families_to_update[family.id]['attributes'].append({
                'attribute': line.attribute_id,
                'group': line.attribute_group_id
            })
            families_to_update[family.id]['groups'].add(line.attribute_group_id.id)

        result = super(FamilyAttributes, self).unlink()

        for family_id, info in families_to_update.items():
            family = info['family']

            for attr_info in info['attributes']:
                if attr_info['attribute'] in family.exist_attribute_ids:
                    family.write({
                        'exist_attribute_ids': [(3, attr_info['attribute'].id)]
                    })

            for group_id in info['groups']:
                remaining_attrs = family.family_attribute_ids.filtered(
                    lambda l: l.attribute_group_id.id == group_id
                )

                if not remaining_attrs:
                    if group_id in family.exist_group_ids.ids:
                        family.write({
                            'exist_group_ids': [(3, group_id)]
                        })

                    if family.family_sequence_id:
                        seq_line = family.family_sequence_id.attr_group_ids.filtered(
                            lambda l: l.attribute_group_id.id == group_id
                        )
                        if seq_line:
                            seq_line.unlink()

            if family.family_sequence_id:
                family.update_view_in_sequence()

        return result


class FamilyAttributeSequence(models.Model):
    _name = 'family.attribute.sequence'
    _description = 'Family Attribute Sequence'

    attr_group_ids = fields.One2many('family.attribute.seq.line',
                                     'family_sequence_id', string="Attribute Group")
    family_id = fields.Many2one('family.attribute', 'Family')
    exist_group_ids = fields.Many2many('attribute.group', related='family_id.exist_group_ids')
    name = fields.Char(related='family_id.name')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        lines = []
        ctx = self.env.context
        family_id = self.env['family.attribute'].search([('id', '=', ctx.get('default_family_id'))])
        groups = self.env['attribute.group'].search([("id", 'in', family_id.exist_group_ids.ids)])

        for grp in groups:
            lines.append((0, 0, {
                'attribute_group_id': grp.id,
            }))
        res['attr_group_ids'] = lines
        return res

    def create(self, vals):
        res = super(FamilyAttributeSequence, self).create(vals)
        res.family_id.family_sequence_id = res.id
        return res

    def confirm_sequence(self):
        for rec in self:
            rec.family_id.update_view_in_sequence()


class FamilyAttributeSequenceLines(models.Model):
    _name = 'family.attribute.seq.line'
    _description = 'Family Attribute Sequence'

    sequence = fields.Integer("Sequence")
    attribute_group_id = fields.Many2one('attribute.group', string='Attribute Group')
    attr_grp_company_id = fields.Many2one(related='attribute_group_id.company_id')
    family_sequence_id = fields.Many2one('family.attribute.sequence', 'Family Sequence')
