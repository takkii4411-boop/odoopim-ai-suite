# -*- coding: utf-8 -*-

import time, pytz
import re
from datetime import datetime, timedelta, timezone, date
from email.policy import default
from markupsafe import Markup
import pytz

from lxml import etree
from odoo import models, api, fields, _, tools
from odoo.exceptions import UserError, ValidationError
import traceback, pdb, inspect
import xml.sax.saxutils as saxutils
import logging

_logger = logging.getLogger(__name__)


class AttributeGroup(models.Model):
    _name = 'attribute.group'
    _description = 'Attribute Group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    name = fields.Char('Name', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    attributes_ids = fields.One2many('product.attribute', 'attribute_group_id', string='Attributes', required=True,
                                     tracking=True, store=True)
    attribute_family_id = fields.Many2many('family.attribute', string='Attribute Family', required=True, tracking=True,
                                           store=True)
    attribute_group_line_ids = fields.One2many('attribute.group.lines', 'attr_group_id',
                                               string='Attribute group line', auto_join=True, tracking=True)
    attribute_code = fields.Selection([('medias', 'Medias')], string="Code")
    attribute_code_rec = fields.Char(string='Code ', readonly=True)
    attribute_label = fields.Char(string='English')
    parent_id = fields.Many2one(
        'attribute.group',
        string='Parent Group',
        ondelete='cascade',
    )
    child_ids = fields.One2many(
        'attribute.group',
        'parent_id',
        compute='_compute_child_ids',
        string='Sub-groups '
    )
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

    is_create_mode = fields.Boolean(default=False, string='Create Mode')

    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def _log_changes(self, vals, action):
        updated_write_date_utc = fields.Datetime.now()
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        updated_write_date = pytz.utc.localize(updated_write_date_utc).astimezone(user_tz).strftime("%d/%m/%Y %H:%M:%S")
        new_write_uid = self.env.user.display_name
        for rec in self:
            changes = []

            tracked_fields = ['name', 'attribute_code_rec', 'active', 'parent_id', 'description', 'attribute_code']
            tracked_group_line_fields = ['product_attribute_id', 'display_type', 'enable', 'is_value_per_channel',
                                         'is_value_per_locale']

            for key in vals:
                if key in tracked_fields:
                    attribute = self._fields[key].string
                    old_value = getattr(rec, key, 'N/A') if action == "update" else 'N/A'
                    new_value = vals[key] or 'N/A'

                    if key == 'parent_id':
                        old_value = rec.parent_id.display_name if rec.parent_id else 'N/A'
                        new_value = self.env['attribute.group'].browse(vals[key]).display_name if vals.get(
                            key) else 'N/A'

                    change_entry = f"""
                        <li>
                            <strong>{attribute}</strong><br>
                            <span style='color: red;'>Old value:</span> {old_value}
                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                            <span style='color: green;'>New value:</span> {new_value}
                        </li>
                    """
                    changes.append(change_entry)

            if 'attribute_group_line_ids' in vals:
                for command in vals['attribute_group_line_ids']:
                    if command[0] == 1:
                        line_id = self.env['attribute.group.lines'].browse(command[1])
                        line_changes = []
                        for field in tracked_group_line_fields:
                            if field in command[2]:
                                old_value = getattr(line_id, field, 'N/A')
                                new_value = command[2][field] or 'N/A'
                                if field == 'product_attribute_id':
                                    old_value = line_id.product_attribute_id.display_name if line_id.product_attribute_id else 'N/A'
                                    new_value = self.env['product.attribute'].browse(
                                        new_value).display_name if new_value else 'N/A'

                                line_changes.append(f"""
                                    <li>
                                        <strong>{line_id._fields[field].string}</strong><br>
                                        <span style='color: red;'>Old:</span> {old_value}
                                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                        <span style='color: green;'>New:</span> {new_value}
                                    </li>
                                """)
                        if line_changes:
                            changes.append(f"""
                                <li>
                                    <strong>Updated Attribute Group Line (ID {line_id.id})</strong>
                                    <ul>{''.join(line_changes)}</ul>
                                </li>
                            """)

                    elif command[0] == 0:
                        new_values = command[2]
                        new_line_changes = []
                        for field in tracked_group_line_fields:
                            if field in new_values:
                                field_label = self.env['attribute.group.lines']._fields[field].string
                                new_value = new_values[field] or 'N/A'
                                old_value = "N/A"
                                if field == 'product_attribute_id':
                                    new_value = self.env['product.attribute'].browse(
                                        new_value).display_name if new_value else 'N/A'
                                new_line_changes.append(f"""
                                    <li>
                                        <strong>{field_label}</strong><br>
                                        <span style='color: red;'>Old value:</span> {old_value}
                                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                        <span style='color: green;'>New value:</span> {new_value}
                                    </li>
                                """)
                        if new_line_changes:
                            changes.append(f"""
                                <li>
                                    <strong>New Attribute Group Line Added:</strong><br>
                                    <ul>{''.join(new_line_changes)}</ul>
                                </li>
                            """)

                    elif command[0] == 2:
                        line_id = self.env['attribute.group.lines'].browse(command[1])
                        removed_line_changes = []
                        for field in tracked_group_line_fields:
                            field_label = line_id._fields[field].string
                            old_value = getattr(line_id, field, 'N/A')
                            new_value = "N/A"
                            if field == 'product_attribute_id':
                                old_value = line_id.product_attribute_id.display_name if line_id.product_attribute_id else 'N/A'
                            removed_line_changes.append(f"""
                                <li>
                                    <strong>{field_label}</strong><br>
                                    <span style='color: red;'>Old value:</span> {old_value}
                                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                    <span style='color: green;'>New value:</span> {new_value}
                                </li>
                            """)
                        if removed_line_changes:
                            changes.append(f"""
                                <li>
                                    <strong>Removed Attribute Group Line:</strong><br>
                                    <ul>{''.join(removed_line_changes)}</ul>
                                </li>
                            """)

            if changes:
                action_text = "Created by" if action == "create" else "Updated by"
                user_info = f"<small>{action_text} <strong>{new_write_uid}</strong> on {updated_write_date}</small>"
                full_message = f"""
                    <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                        {user_info}
                        <ul style="list-style-type: none; padding-left: 0;">{''.join(changes)}</ul>
                    </div>
                """
                rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')
                return full_message
            return None

    def write(self, vals):
        # Skip sync if coming from group line
        for rec in self:
            rec._log_changes(vals, action="update")
        result = super(AttributeGroup, self).write(vals)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['attribute_code_rec'] = self.env['ir.sequence'].next_by_code('attribute.group') or None
        records = super(AttributeGroup, self).create(vals_list)
        for rec, vals in zip(records, vals_list):
            rec._log_changes(vals, action="create")
        return records

    # @api.depends('name')
    # def _compute_label_translation(self):
    #     translator = Translator()
    #     for record in self:
    #         if record.name:
    #             try:
    #                 user_lang = self.env.user.lang
    #                 lang_rec = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
    #                 src_lang = lang_rec.url_code
    #                 translation = translator.translate(record.name, src=src_lang, dest='en')
    #                 record.attribute_label = translation.text.capitalize()
    #             except Exception as e:
    #                 record.attribute_label = 'Error in translation'
    #         else:
    #             record.attribute_label = ''

    # this is for loading tree view in while click edit button
    def _compute_child_ids(self):
        for record in self:
            record.child_ids = self.env['attribute.group'].search([('company_id', '=', self.env.company.id)])

    # attribute group edit button
    def attribute_group_open_form_view(self):
        all_attribute_group_ids = self.env['attribute.group'].search([]).ids
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Attribute Group',
            'res_model': 'attribute.group',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
            'context': {'no_breadcrumbs': True,
                        'default_is_create_mode': False,
                        },
            'res_id': self.id,
        }

    # delete button group
    def attribute_group_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'attribute.group.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_group_id': self.id},
        }

    def action_back_to_menu(self):
        menu_id = self.env.ref('pim_ext.menu_pim_attribute_group')

        # return {
        #      'type': 'ir.actions.act_window',
        #      'res_model': 'attribute.group',
        #      'view_mode': 'list',
        #      'view_id': action_id,
        #      # 'context': {'no_breadcrumbs': True},
        #      'target': 'current',
        # }
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    def save_attributes(self):
        # self.update_attribute_group_view()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'attribute.group',
            'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
            'res_id': self.id,
            'context': {'no_breadcrumbs': True},
            'target': 'current',
        }

    def update_attribute_group_view(self):
        attr_grp = self or self.env['attribute.group'].sudo().search(
            [('id', 'in', self.env.context['active_ids'])], order="id asc")
        widgets_mapping = {
            'image': 'image',
            'multi_select': 'many2many_tags',
            'color': 'color_picker',
            'price': 'monetary',
        }
        views = self.env['ir.ui.view']
        for rec in attr_grp:
            company_name = rec.company_id.name
            group_name = rec.name
            safe_group_name = saxutils.escape(group_name)
            safe_group_id = group_name.lower().replace(' ', '_').replace('&', 'and')
            family_group_list = self.env['family.attribute'].search([('exist_group_ids', 'in', rec.id)])
            if family_group_list:
                family_condition = f'''family_id not in {family_group_list.ids}'''
                updated_invisible = f"{family_condition}"

            else:
                updated_invisible = f"1"

            form_arch = f'''
                        <xpath expr="//notebook/page[@id='attributes_page']" position="inside">
                        <group name="{safe_group_id}" id="{safe_group_id}" string="{safe_group_name}" invisible="{updated_invisible}" collapsible="1" expanded="1" >
                        '''
            # Add fields with appropriate widget
            for line in rec.attribute_group_line_ids:
                attr = line.product_attribute_id
                widget = widgets_mapping.get(attr.display_type)
                field_tag = ''
                # self.attribute_field_xml(attr, widget)
                family_list = self.env['family.attribute'].search([('exist_attribute_ids', 'in', attr.id)])
                if attr.original_name and attr.display_type != 'table':
                    field_tag += f'''<field name="{attr.original_name}"'''
                    if family_list:
                        field_tag += f''' invisible="family_id not in {family_list.ids}"'''
                    else:
                        field_tag += f''' invisible="1"'''

                    if attr.widget:
                        field_tag += f''' widget="{widget}"'''
                    if attr.is_mandatory:
                        field_tag += f''' required="0"'''
                    if attr.display_type in ['simple_select', 'multi_select']:
                        field_tag += f" options='{{\"no_create_edit\": True, \"no_edit\": True, \"no_open\": True}}'"
                        # field_tag += f''' options="{'no_quick_create': True, 'no_create_edit': True, 'no_open': True}"'''
                    field_tag += f'''/>\n'''
                # elif attr.original_name and attr.display_type == 'table':
                #    For Adding one2many table design
                #     field_tag += f'''<field name="{attr.original_name}"'''
                #     field_tag += f'''options='{{\"no_create_edit\": True, \"no_edit\": True, \"no_open\": True}}'/>\n'''

                form_arch += field_tag

            form_arch += '''
                        </group>
                        </xpath>'''
            default_view_id = self.env.ref('pim_ext.view_product_creation_split_view_custom').id
            # Create or update the view
            view_name = f"product_attribute_{company_name.lower().replace(' ', '_')}_{safe_group_id}"
            existing_view = views.search([
                ('name', '=', view_name),
                ('model', '=', 'product.template')
            ], limit=1)

            if existing_view:
                existing_view.arch = form_arch
            else:
                existing_view = views.sudo().create({
                    'name': view_name,
                    'type': 'form',
                    'model': 'product.template',
                    'inherit_id': default_view_id,
                    'active': True,
                    'arch': form_arch,
                })

    def create_pim_attribute_groups(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Attribute group',
            'res_model': 'attribute.group',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
            'target': 'current',
            'context': {
                'default_is_create_mode': True,
                'default_child_ids': self.env['attribute.group'].search([('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def update_attributes_according_to_mapped_groups(self):
        attribute_group = self or self.env['attribute.group'].search([('id', '=', self.env.context['active_ids'])])
        """Sync and validate attribute groups with product.attribute considering company_id"""
        for group in attribute_group:
            # Collect all attributes from lines
            line_attributes = group.attribute_group_line_ids.mapped('product_attribute_id')
            # attributes in lines should have the group assigned
            for attr in line_attributes:
                if attr.company_id == group.company_id:
                    if group not in attr.attribute_group:
                        attr.write({'attribute_group': [(4, group.id)]})  # add group

            # attributes that have this group should exist in group lines
            attrs_with_group = self.env['product.attribute'].search([
                ('attribute_group', 'in', group.id),
                ('company_id', '=', group.company_id.id)
            ])
            for attr in attrs_with_group:
                if attr not in line_attributes:
                    # Create missing line (only for same company)
                    self.env['attribute.group.lines'].create({
                        'attr_group_id': group.id,
                        'product_attribute_id': attr.id,
                    })

    def remove_other_company_attributes(self):
        attribute_group = self or self.env['attribute.group'].search([('id', '=', self.env.context['active_ids'])])
        for rec in attribute_group:
            if rec.attribute_group_line_ids:
                for g in rec.attribute_group_line_ids:
                    if g.product_attribute_id.company_id.id == rec.company_id.id:
                        pass
                    else:
                        g.unlink()

    def remove_attribute_view(self, attribute_id):
        for rec in self:
            company_name = rec.company_id.name
            group_name = rec.name
            view_name = f'product_attribute_{company_name.lower().replace(" ", "_")}_{group_name.lower().replace(" ", "_")}'
            view = self.env['ir.ui.view'].search([
                ('name', '=', view_name),
                ('model', '=', 'product.template')
            ], limit=1)

            if view:
                # Parse XML
                arch = etree.XML(view.arch)
                field_node = arch.xpath(f"//field[@name='{attribute_id.original_name}']")
                if field_node:
                    parent = field_node[0].getparent()
                    parent.remove(field_node[0])
                    view.arch = etree.tostring(arch, encoding='unicode')

    # Old Codes
    # @api.model
    # def create(self, vals):
    #      record = super(Attributegroup, self).create(vals)
    #      record._check_unique_attributes()
    #      return record
    #
    # @api.model
    # def write(self, vals):
    #      res = super(Attributegroup, self).write(vals)
    #      if 'attribute_group_line_ids' in vals:
    #           self._check_unique_attributes()
    #      return res
    #
    # @api.constrains('attribute_group_line_ids')
    # def _check_unique_attributes(self):
    #      for record in self:
    #           attributes_in_group = record.attribute_group_line_ids.mapped('product_attribute_id')
    #           for attribute in attributes_in_group:
    #                other_groups = self.env['attribute.group'].search([
    #                     ('id', '!=', record.id),
    #                     ('attribute_group_line_ids.product_attribute_id', '=', attribute.id)
    #                ])
    #                if other_groups:
    #                     raise ValidationError(
    #                          f"The attribute '{attribute.name}' is already assigned to another attribute group."
    #                     )


class AttributeGroupLine(models.Model):
    _name = 'attribute.group.lines'
    _description = "Attribute group lines"
    _rec_name = "name"

    attr_group_id = fields.Many2one('attribute.group', string='Attribute Group')
    name = fields.Char(related="product_attribute_id.name")
    used_attribute_ids = fields.Many2many(
        'product.attribute',
        string='Used Attributes',
        store=False
    )
    product_attribute_id = fields.Many2one('product.attribute', string='Product Attribute')
    attribute_company_id = fields.Many2one(related='product_attribute_id.company_id')
    display_type = fields.Selection(
        selection=[
            ('radio', 'Radio'),
            ('date', 'Date'),
            ('file', 'File'),
            ('identifier', 'Identifier'),
            ('image', 'Image'),
            ('measurement', 'Measurement'),
            ('multi_select', 'Multi Select'),
            ('link', 'Link'),
            ('number', 'Integer'),
            ('price', 'Price'),
            ('ref_data_multi', 'Reference Data Multi Select'),
            ('ref_data_simple_select', 'Reference Data Simple Select'),
            ('simple_select', 'Simple Select'),
            ('text', 'Text'),
            ('textarea', 'Text Area'),
            ('yes_no', 'Checkbox'),
            ('pills', 'Pills'),
            ('select', 'Select'),
            ('color', 'Color'),
            ('multi', 'Multi-checkbox (option)'),
            ('float', 'Float'),
        ],
        help="The display type used in the Product Configurator.")

    related_display_type = fields.Selection(
        related='product_attribute_id.display_type',
        store=True,
        readonly=True
    )

    enable = fields.Boolean(string="Enable", default=True)
    value_per_channel = fields.Boolean(string="Value per channel", default=False,
                                       related="product_attribute_id.is_value_per_channel")
    value_per_locale = fields.Boolean(string="Value per locale", default=False,
                                      ralated="product_attribute_id.is_value_per_locale")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.product_attribute_id and rec.attr_group_id:
                rec.product_attribute_id.attribute_group = [(4, rec.attr_group_id.id)]
                # rec.attr_group_id.update_attribute_group_view()

        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.product_attribute_id and rec.attr_group_id:
                if rec.attr_group_id not in rec.product_attribute_id.attribute_group:
                    rec.product_attribute_id.attribute_group = [(4, rec.attr_group_id.id)]
        return res

    def unlink(self):
        for rec in self:
            if rec.product_attribute_id and rec.attr_group_id:
                if rec.attr_group_id in rec.product_attribute_id.attribute_group:
                    rec.attr_group_id.remove_attribute_view(rec.product_attribute_id)
                    rec.product_attribute_id.write({
                        'attribute_group': [(3, rec.attr_group_id.id)]
                    })

        return super().unlink()


class AttributeGroupUnlinkWizard(models.TransientModel):
    _name = 'attribute.group.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Attribute Group'

    group_id = fields.Many2one('attribute.group', string="Attribute Group")

    def confirm_unlink(self):
        menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Attributes Groups')])
        if self.group_id:
            self.group_id.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }
