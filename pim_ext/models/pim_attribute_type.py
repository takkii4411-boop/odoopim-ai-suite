# -*- coding: utf-8 -*-
from random import randint
from odoo import models, api, fields, _, tools
import pytz
import colorsys
from odoo.exceptions import ValidationError
import re


class PIMAttributeType(models.Model):
    _name = 'pim.attribute.type'
    _description = 'PIM Attribute Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Attribute Name", default=' ')
    type_name = fields.Char(string="Attribute Type Name")
    attribute_types_id = fields.Many2one('pim.attribute.type', string='Parent Attributes', index=True,
                                         ondelete="cascade")
    attribute_ids = fields.One2many('pim.attribute.type', 'attribute_types_id', string='Attributes')
    is_invisible = fields.Boolean(default=False, string='Invisible Types')
    attribute_group = fields.Many2one('attribute.group', string='Attribute Group', tracking=True)
    attribute_types = fields.Selection([('basic', 'Basic'), ('optional', 'Optional')], string='Attribute Type')
    is_mandatory = fields.Boolean(string='Mandatory', default=False)
    is_required_in_clone = fields.Boolean(string='Required in Clone', default=True)
    is_cloning = fields.Boolean(string='Cloning', default=True)
    is_completeness = fields.Boolean(string='Completeness')
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
        ],
        help="The display type used in the Product Configurator.")

    master_attribute_ids = fields.One2many(
        'product.attribute',
        'parent_id',
        compute='_compute_master_attribute_ids',
        string='Attributes'
    )

    code = fields.Char(string='Code', readonly=True)
    original_name = fields.Char('Field Names')
    unique_value = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Unique Value',
        default='no'
    )
    value_per_channel = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Value per channel',
        default='no'
    )
    is_value_per_channel = fields.Boolean("Value Per Channel")
    is_value_per_locale = fields.Boolean("Value Per Locale")
    value_per_locale = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Value per locale',
        default='no'
    )
    usable_in_grid = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Usable in grid',
        default='no'
    )
    locale_specific = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Locale specific',
        default='no'
    )
    value_ids = fields.One2many(
        comodel_name='pim.attribute.value',
        inverse_name='attribute_type_id',
        string="Values", copy=True)
    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def _compute_master_attribute_ids(self):
        for record in self:
            record.master_attribute_ids = self.env['product.attribute'].search(
                [('company_id', '=', self.env.company.id)])

    def _compute_attribute_ids(self):
        for record in self:
            record.attribute_ids = self.env['pim.attribute.type'].search([])

    def sort_colors(self):
        for record in self:
            colors_rgb = [tuple(int(rec.html_color[i:i + 2], 16) for i in (1, 3, 5)) for rec in record.value_ids]
            colors_hsv = [colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0) for r, g, b in colors_rgb]
            sorted_colors_hsv = sorted(colors_hsv, key=lambda x: (x[0], x[1], x[2]))
            sorted_colors_rgb = [colorsys.hsv_to_rgb(h, s, v) for h, s, v in sorted_colors_hsv]
            sorted_colors_rgb = [(round(r * 255), round(g * 255), round(b * 255)) for r, g, b in sorted_colors_rgb]
            # # Clear existing sorted colors
            vals_list = []
            for r, g, b in sorted_colors_rgb:
                color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                record_name = self.env['pim.attribute.value'].search([('html_color', '=', color),
                                                                      ('attribute_type_id', '=', record.id)],
                                                                     order="id", limit=1)
                vals_list.append((0, 0, {
                    'name': record_name.name,
                    'html_color': color,
                    'attribute_type_id': record.id,
                    'image': record_name.image
                }))
            record.value_ids.unlink()
            record.value_ids = vals_list

    def _log_changes(self, rec, vals, action):
        # Get the current time in UTC
        updated_write_date_utc = fields.Datetime.now()
        # Convert to the user's timezone
        user_tz = self.env.user.tz or 'UTC'  # Default to UTC if no timezone is set
        updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")

        new_write_uid = self.env.user.display_name
        changes = []  # Store changes in list

        # Filter out relational fields (like One2many, Many2one, etc.) from vals for the SQL query
        direct_fields = [key for key in vals.keys() if key in rec._fields and not isinstance(rec._fields[key], (
            fields.Many2one, fields.One2many, fields.Many2many))]

        # Fetch old values directly from the database for direct fields only
        if direct_fields:
            query = f"SELECT {', '.join(direct_fields)} FROM {rec._table} WHERE id = %s"
            rec.env.cr.execute(query, (rec.id,))
            old_values = dict(zip(direct_fields, rec.env.cr.fetchone()))
        else:
            old_values = {}

        # Track changes in direct fields
        for key in vals:
            if key in [
                'name', 'code', 'attribute_group', 'display_type',
                'is_mandatory', 'is_required_in_clone', 'is_completeness',
                'unique_value', 'is_value_per_channel', 'is_value_per_locale',
                'usable_in_grid', 'locale_specific'
            ]:
                attribute = rec._fields[key].string

                if key == 'attribute_group':
                    # Handle Many2one field (attribute_group)
                    old_group_id = old_values.get(key)  # Get the ID of the attribute group
                    old_value = self.env['attribute.group'].browse(
                        old_group_id).display_name if old_group_id else 'N/A'
                    new_group_id = vals.get(key)  # Get the new ID from vals
                    new_value = self.env['attribute.group'].browse(
                        new_group_id).display_name if new_group_id else 'N/A'
                else:
                    # Retrieve the old value from the pre-fetched old_values
                    old_value = old_values.get(key, 'N/A') if action == "update" else 'N/A'
                    new_value = vals[key] or 'N/A'
                # Formatting Old & New values on the same line with space
                change_entry = f"""
                   <li>
                       <strong>{attribute}</strong><br>
                       <span style='color: red;'>Old value:</span> {old_value}  
                            
                       <span style='color: green;'>New value:</span> {new_value}
                   </li>
               """
                changes.append(change_entry)

        # Track changes in value_ids (One2many field)
        if 'value_ids' in vals:
            for command in vals['value_ids']:
                if command[0] == 1:  # Update existing record
                    value_record = rec.value_ids.browse(command[1])
                    for field in command[2]:
                        field_label = value_record._fields[field].string
                        old_value = getattr(value_record, field, 'N/A')
                        new_value = command[2][field] if command[2][field] is not None else 'N/A'

                        if isinstance(value_record._fields[field], fields.Many2one):
                            old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                            new_value = self.env[value_record._fields[field].comodel_name].browse(
                                new_value).display_name if new_value != 'N/A' else 'N/A'
                        elif isinstance(value_record._fields[field], fields.Many2many):
                            old_value = ', '.join(old_value.mapped('display_name')) if old_value else 'N/A'
                            if isinstance(new_value, (list, tuple)):
                                ids = [cmd[1] if isinstance(cmd, tuple) and cmd[0] in (1, 4) else cmd
                                       for cmd in new_value if isinstance(cmd, (int, tuple))]
                                new_value = ', '.join(
                                    self.env[value_record._fields[field].comodel_name].browse(ids).mapped(
                                        'display_name')) if ids else 'N/A'
                            else:
                                new_value = new_value if new_value is not None else 'N/A'

                        change_entry = f"""
                         <li>
                             <strong>{field_label} (in Value)</strong><br>
                             <span style='color: red;'>Old value:</span> {old_value}  
                                  
                             <span style='color: green;'>New value:</span> {new_value}
                         </li>
                     """
                        changes.append(change_entry)

                elif command[0] == 0:  # New record added
                    new_vals = command[2]
                    for field in new_vals:
                        field_label = self.env['pim.attribute.value']._fields[field].string
                        new_value = new_vals.get(field, 'N/A') if field in new_vals else 'N/A'
                        old_value = 'N/A'  # New records have no old value

                        if isinstance(self.env['pim.attribute.value']._fields[field], fields.Many2one):
                            new_value = self.env[
                                self.env['pim.attribute.value']._fields[field].comodel_name].browse(
                                new_value).display_name if new_value != 'N/A' else 'N/A'
                        elif isinstance(self.env['pim.attribute.value']._fields[field], fields.Many2many):
                            if isinstance(new_value, (list, tuple)):
                                ids = [cmd[1] if isinstance(cmd, tuple) and cmd[0] in (1, 4) else cmd
                                       for cmd in new_value if isinstance(cmd, (int, tuple))]
                                new_value = ', '.join(self.env[self.env['pim.attribute.value']._fields[
                                    field].comodel_name].browse(ids).mapped('display_name')) if ids else 'N/A'
                            else:
                                new_value = new_value if new_value is not None else 'N/A'

                        change_entry = f"""
                         <li>
                             <strong>{field_label} (in New Value)</strong><br>
                             <span style='color: red;'>Old value:</span> {old_value}  
                                  
                             <span style='color: green;'>New value:</span> {new_value}
                         </li>
                     """
                        changes.append(change_entry)

                elif command[0] == 2:  # Deletion
                    # Browse the record from the current value_ids before it’s removed
                    removed_record = rec.value_ids.filtered(lambda r: r.id == command[1])
                    if removed_record:
                        # Define the fields you want to log for the removed record
                        fields_to_log = ['name', 'sequence', 'value', 'color', 'image']  # Adjust based on your model
                        for field in fields_to_log:
                            if field in removed_record._fields:
                                field_label = removed_record._fields[field].string
                                old_value = getattr(removed_record, field, 'N/A')
                                new_value = 'N/A'  # Removed records have no new value

                                # Handle special field types
                                if isinstance(removed_record._fields[field], fields.Many2one):
                                    old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                                elif isinstance(removed_record._fields[field], fields.Many2many):
                                    old_value = ', '.join(
                                        old_value.mapped('display_name')) if old_value else 'N/A'
                                elif old_value is False:
                                    old_value = 'False'  # Explicitly show False as a string
                                elif old_value is None:
                                    old_value = 'N/A'

                                change_entry = f"""
                                 <li>
                                     <strong>{field_label} (in Removed Value)</strong><br>
                                     <span style='color: red;'>Old value:</span> {old_value}  
                                          
                                     <span style='color: green;'>New value:</span> {new_value}
                                 </li>
                                 """
                                changes.append(change_entry)
                    else:
                        # Fallback: If the record is already gone, log the ID only
                        change_entry = f"""
                         <li>
                             <strong>Removed Value</strong><br>
                             <span style='color: red;'>Old value:</span> Record ID {command[1]}  
                                  
                             <span style='color: green;'>New value:</span> N/A
                         </li>
                         """
                        changes.append(change_entry)

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

    def write(self, vals):
        res = super(PIMAttributeType, self).write(vals)

        # Fields that need to be updated in product.attribute
        fields_to_update = [
            'is_mandatory', 'is_required_in_clone', 'is_cloning', 'is_completeness'
        ]

        # Check if any of these fields were modified
        update_needed = any(field in vals for field in fields_to_update)

        if update_needed:
            for record in self:
                product_attr = self.env['product.attribute'].search([('name', '=', record.name)], limit=1)
                if product_attr:
                    update_vals = {field: record[field] for field in fields_to_update if field in vals}
                    product_attr.write(update_vals)

        # Log changes (existing functionality)
        for rec in self:
            self._log_changes(rec, vals, action="update")

        return res

    @api.model_create_multi
    def create(self, vals_list):
        # for vals in vals_list:
        #     vals['code'] = self.env['ir.sequence'].next_by_code('pim.attribute.type') or None

        records = super(PIMAttributeType, self).create(vals_list)

        for record, vals in zip(records, vals_list):
            self._log_changes(record, vals, action="create")

        return records

    def attribute_edit_open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Attribute',
            # 'res_model': 'product.attribute',
            'view_mode': 'form',
            'res_model': 'pim.attribute.type',
            'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
            'context': {'no_breadcrumbs': True},
            'res_id': self.id,
        }

    def attribute_master_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'attribute.master.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attribute_types_id': self.id},
        }

    def create_pim_attribute_type(self):
        # Return the action to open the product.attribute custom layout
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Attribute',
            'res_model': 'pim.attribute.type',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
            'target': 'current',
            'context': {
                'default_attribute_ids': self.env['pim.attribute.type'].search([]).ids,
                'no_breadcrumbs': True
            },
        }

    def sanitize_field_name(self, name):
        name = name.lower()
        name = name.replace(' #', '_1')
        name = re.sub(r'[^a-z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        name = f'x_{name}'
        if not name[0].isalpha():
            name = 'x_' + name
        return name[:63]

    def create_attributes(self):
        self.ensure_one()
        for vals in self:
            self.original_name = self.sanitize_field_name(vals.name)
            model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.management')])
            d_type = ''

            if vals['display_type']:
                if vals['display_type'] in ['select', 'color']:
                    d_type = 'selection'

                elif vals['display_type'] in ['text']:
                    d_type = 'char'

                elif vals['display_type'] in ['textarea']:
                    d_type = 'text'
                elif vals['display_type'] in ['date']:
                    d_type = 'date'

                elif vals['display_type'] in ['number']:
                    d_type = 'integer'

                elif vals['display_type'] in ['link', 'file', 'image']:
                    d_type = 'binary'

                elif vals['display_type'] in ['yes_no']:
                    d_type = 'boolean'

                elif vals['display_type'] in ['simple_select']:
                    d_type = 'many2one'
                elif vals['display_type'] in ['multi_select']:
                    d_type = 'many2many'
                elif vals['display_type'] in ['price']:
                    d_type = 'monetary'

            if d_type == 'many2one':
                create_vals = {
                    'name': vals.original_name,
                    'field_description': vals['name'],
                    'model': model_id.model,
                    'model_id': model_id.id,
                    'ttype': d_type,
                    'relation': 'pim.attribute.value',
                    'domain': '[("attribute_type_id", "=", %d)]' % vals.id,
                }
            elif d_type == 'many2many':
                create_vals = {
                    'name': vals.original_name,
                    'field_description': vals['name'],
                    'model': model_id.model,
                    'model_id': model_id.id,
                    'ttype': d_type,
                    'relation': 'pim.attribute.value',
                    'domain': '[("attribute_type_id", "=", %d)]' % vals.id,
                }
            else:
                create_vals = {
                    'name': vals.original_name,
                    'field_description': vals.name,
                    'model_id': model_id.id,
                    'ttype': d_type,
                }
            print("create_vals === ", create_vals)
            create_field = self.env['ir.model.fields'].sudo().create(create_vals)

            if d_type == 'selection' and vals.value_ids:

                for rec in vals.value_ids:
                    sel_name = rec[2]['name']
                    sel_value = rec[2]['name']
                    sel_val = self.env['ir.model.fields.selection'].sudo().create({
                        'name': sel_name,
                        'value': sel_value,
                        'field_id': create_field.id
                    })

            # creates a filename field for binary field
            if d_type == 'binary':
                file_name = vals.original_name + '_file_name'
                create_vals_file = {'name': file_name,
                                    'field_description': vals.name,
                                    'model_id': model_id,
                                    'ttype': 'char',
                                    }
                create_field_file_name = self.env['ir.model.fields'].sudo().create(create_vals_file)

        # # Check if an existing attribute exists
        # existing_attribute = attribute.search([('name', '=', self.name)], limit=1)
        #
        # if existing_attribute:
        #      # Update existing attribute
        #      existing_attribute.write(attribute_vals)
        #      attribute = existing_attribute
        # else:
        #      # Create new attribute
        #      attribute = attribute.create(attribute_vals)
        #
        # # Ensure attribute group lines are updated
        # if self.attribute_group:
        #      group_line = self.env['attribute.group.lines'].search([
        #           ('attr_group_id', '=', self.attribute_group.id),
        #           ('product_attribute_id', '=', attribute.id),
        #      ], limit=1)
        #
        #      if not group_line:
        #           self.env['attribute.group.lines'].create({
        #                'attr_group_id': self.attribute_group.id,
        #                'product_attribute_id': attribute.id,
        #           })
        # for record in self:
        #      if record.display_type in ['simple_select', 'radio', 'pills', 'color',
        #                                 'multi_select'] and not record.value_ids:
        #           raise ValidationError(
        #                "Please fill the Attribute values for dropdown.")
        #
        # menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
        # return {
        #      'type': 'ir.actions.client',
        #      'tag': 'reload',
        #      'params': {
        #           'menu_id': menu_id.id,
        #      },
        # }

    def action_back_to_menu_attribute(self):
        self.ensure_one()
        menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
        if not self.name or self.name.strip() == '' and not self.display_type:
            self._cr.execute("DELETE FROM pim_attribute_type WHERE id = %s", (self._origin.id,))
            self._cr.commit()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'menu_id': menu_id.id,
                },
            }
        elif self.display_type and self.name.strip() == '':
            raise ValidationError("You should fill the attribute name.")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    def action_select_date(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'date',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_file(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'file',
                'default_attribute_types_id': self.id,
                'default_widget': 'image',
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_identifier(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'text',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_image(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'image',
                'default_attribute_types_id': self.id,
                'default_widget': 'image',
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_table(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'table',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_measurement(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'measurement',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    # def action_select_measurement(self):
    #      self.ensure_one()
    #      return {
    #           'type': 'ir.actions.act_window',
    #           'name': 'Measurement Attribute',
    #           'res_model': 'pim.attribute.type',
    #           'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
    #           'view_mode': 'form',
    #           'context': {
    #                'default_attribute_ids': self.env['product.attribute'].search([]).ids,
    #                'default_is_invisible': True,
    #                'default_display_type': 'measurement',
    #                'default_type_name': 'Measurement',
    #           },
    #      }

    def action_select_link(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'link',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_multiselect(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'multi_select',
                'default_attribute_types_id': self.id,
                'default_widget': 'many2many_tags',
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_number(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'number',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_float(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'float',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_price(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'price',
                'default_attribute_types_id': self.id,
                'default_widget': 'monetary',
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_ref_data_multi(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'price',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_ref_data_simple(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'price',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_multi_checkbox(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'price',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_multi_color(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'color',
                'default_attribute_types_id': self.id,
                'widget': 'color_picker',
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_radio(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'price',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_simple(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'simple_select',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_text(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'text',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_text_area(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'textarea',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    def action_select_yes_no(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Attribute',
            'res_model': 'product.attribute',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
                'default_display_type': 'yes_no',
                'default_attribute_types_id': self.id,
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }


class PimAttributeValue(models.Model):
    _name = 'pim.attribute.value'
    _description = 'Pim Attribute Value'

    def _get_default_color(self):
        return randint(1, 11)

    attribute_type_id = fields.Many2one('pim.attribute.type', ondelete='cascade',
                                        required=True,
                                        index=True)
    name = fields.Char(string="Value", required=True, translate=True)
    sequence = fields.Integer(string="Sequence", help="Determine the display order", index=True)
    html_color = fields.Char(
        string="Color",
        help="Here you can set a specific HTML color index (e.g. #ff0000)"
             " to display the color if the attribute type is 'Color'.")
    display_type = fields.Selection(related='attribute_type_id.display_type')
    color = fields.Integer(string="Color Index", default=_get_default_color)
    image = fields.Image(
        string="Image",
        help="You can upload an image that will be used as the color of the attribute value.",
        max_width=70,
        max_height=70,
    )
