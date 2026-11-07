# -*- coding: utf-8 -*-

import time, pytz
import re
from datetime import datetime, timedelta, timezone, date
from email.policy import default
from markupsafe import Markup
import pytz
import colorsys

from lxml import etree

from odoo import models, api, fields, _, tools
from odoo.exceptions import UserError, ValidationError
import traceback, pdb, inspect

import logging

_logger = logging.getLogger(__name__)

FIELD_WIDGETS = {
    'image': 'image',
    'file': 'binary',
    'multi_select': 'many2many_tags',
    'color': 'pim_color',
    'price': 'monetary',
    'yes_no': 'boolean',
    'date': 'date',
}


class AttributeForm(models.Model):
    _inherit = 'product.attribute'
    _rec_name = 'name'

    display_type = fields.Selection(
        selection_add=[
            ('date', 'Date'),
            ('file', 'File'),
            ('image', 'Image'),
            ('measurement', 'Measurement'),
            ('number', 'Integer'),
            ('price', 'Price'),
            ('text', 'Text'),
            ('textarea', 'Text Area'),
            ('yes_no', 'Checkbox'),
            ('table', 'Table'),
            ('multi_select', 'Multi Select'),
            ('simple_select', 'Simple Select'),
            ('float', 'Float'),
            ('identifier', 'Identifier'),
        ],
        ondelete={
            'date': 'cascade',
            'file': 'cascade',
            'image': 'cascade',
            'measurement': 'cascade',
            'number': 'cascade',
            'price': 'cascade',
            'text': 'cascade',
            'textarea': 'cascade',
            'yes_no': 'cascade',
            'table': 'cascade',
            'multi_select': 'cascade',
            'simple_select': 'cascade',
            'float': 'cascade',
            'table': 'cascade',
            'identifier': 'cascade',
        },
    )
    attribute_group_id = fields.Many2one('attribute.group', string='Group')

    @api.model
    def _attribute_group_domain(self):
        return [('company_id', '=', self.env.company.id)]

    attribute_group = fields.Many2many('attribute.group',
                                       string='Attribute Group', tracking=True,
                                       domain=_attribute_group_domain)
    attribute_type_id = fields.Many2one('pim.attribute.type', string='PIM Attribute Type')
    parent_attribute_id = fields.Many2one('product.attribute', string='Attribute')
    is_mandatory = fields.Boolean(string='Mandatory', default=False)
    is_required_in_clone = fields.Boolean(string='Required in Clone', default=True)
    is_cloning = fields.Boolean(string='Cloning', default=True)
    is_completeness = fields.Boolean(string='Completeness', default=False)

    is_ai_enrichable = fields.Boolean(
        string="AI Enrichable",
        store=True,
    )

    attribute_types = fields.Selection([('basic', 'Basic'),
                                        ('optional', 'Optional')], string='Attribute Type')
    attribute_types_id = fields.Many2one('pim.attribute.type', string='Attribute Type')
    completed_in_percent = fields.Float('Completed Progressbar')
    state = fields.Selection([('unpublish', 'Unpublish'), ('publish', 'Publish')], string='Status', default='unpublish')

    position_ref_field_id = fields.Many2one("ir.model.fields", string="Position After",
                                            domain="[('model_id.model','=','product.management')]")
    # product field to connect and update (AMC)
    product_template_field_id = fields.Many2one("ir.model.fields", "Product Template Field")
    product_product_field_id = fields.Many2one("ir.model.fields", "Product Product Field")

    code = fields.Char(string='Code', readonly=False)

    unique_value = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Unique Value', default='no'
    )

    value_per_channel = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Value per channel', default='no'
    )
    # TODO remove it as per changing to boolean we dont need selections

    is_value_per_channel = fields.Boolean("Value Per Channel")
    is_value_per_locale = fields.Boolean("Value Per Locale")
    is_usable_in_grid = fields.Boolean("Usable in Grid")

    value_per_locale = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Value per locale', default='no'
    )

    usable_in_grid = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Usable in grid', default='no'
    )

    locale_specific = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Locale specific', default='no'
    )
    multi_field_per_value = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Field Per Value', default='no'
    )

    master_attribute_ids = fields.One2many(
        'product.attribute',
        'parent_id',
        compute='_compute_master_attribute_ids',
        string='Attributes'
    )

    parent_id = fields.Many2one(
        'product.attribute',
        string='Parent Group',
        ondelete='cascade',
    )

    sub_attribute_ids = fields.One2many(
        'product.attribute',
        'parent_id',
        string='Table Attributes'
    )


    label_transaltion = fields.Char(string='English', compute="_compute_label_attribute_translation")

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

    products_id = fields.Many2one('product.template', string='Products')

    original_name = fields.Char('Field Names')

    widget = fields.Char("Widget")
    max_value = fields.Char("Max Length")
    alpha_numeric_value = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Alpha Numeric', default='no'
    )



    def attribute_master_form_view(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attribute Form',
            'view_mode': 'form',
            'res_model': 'product.attribute',
            'res_id': self.id,
            'target': 'current',
            'views': [(self.env.ref(
                'pim_ext.view_product_attribute_master_custom').id, 'form')],
        }

    def _get_company_id(self):
        return self.env.company.id

    company_id = fields.Many2one('res.company', required=True, readonly=True,
                                 default=_get_company_id)

    def action_set_values(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Attribute',
            'res_model': 'product.attribute',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'pim_ext.view_product_attribute_master_custom').id,
            'context': {'no_breadcrumbs': True},
            'res_id': self.id,
            'target': 'new'
        }

    def action_add_attribute_value(self):
        """
        Action to add a new attribute value/option line.
        Stays on Options tab and focuses on the new line.
        """
        self.ensure_one()

        # Get the next sequence number
        max_sequence = 0
        if self.value_ids:
            max_sequence = max(self.value_ids.mapped('sequence') or [0])

        # Create a new attribute value
        new_value = self.env['product.attribute.value'].create({
            'attribute_id': self.id,
            'display_type': self.display_type,
            'name': '',  # Empty name - user will fill it
            'sequence': max_sequence + 1,
        })

        # Return action that reopens the form on the Options tab with the new line focused
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.attribute',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_active_notebook_tab': 'options',  # Try to open Options tab
                'focus_field': 'value_ids',  # Try to focus on value_ids field
                'new_value_id': new_value.id,  # Pass the new value ID
            }
        }

    def js_add_value_line(self):
        """
        Simpler method that just creates the value and returns True.
        Best used with JavaScript to handle the UI update without reload.
        """
        self.ensure_one()

        # Get the next sequence number
        max_sequence = 0
        if self.value_ids:
            max_sequence = max(self.value_ids.mapped('sequence') or [0])

        # Create a new attribute value
        self.env['product.attribute.value'].create({
            'attribute_id': self.id,
            'display_type': self.display_type,
            'name': '',
            'sequence': max_sequence + 1,
        })

        # Return True - JS will handle the refresh
        return True

    @api.constrains("value_ids", "value_ids.html_color")
    def check_attribute_values(self):
        """Checks for duplicated colors in attribute values given"""
        for rec in self:
            if rec.display_type in ['color']:
                color_duplicate = []
                name_duplicate = []
                for val in rec.value_ids:
                    if not val.html_color:
                        raise ValidationError(_("Please select a shade for %s to continue." % val.name))
                    if val.html_color in color_duplicate:
                        raise ValidationError(_("Color Already exist please choose a different color [%s]" % val.name))
                    if val.name in name_duplicate:
                        raise ValidationError(
                            _("Name Already exist please choose a different Name for the color %s" % val.name))
                    color_duplicate.append(val.html_color)
                    name_duplicate.append(val.name)

    # this is for loading tree view in while click edit button
    def _compute_master_attribute_ids(self):
        for record in self:
            record.master_attribute_ids = self.env['product.attribute'].search(
                [('company_id', '=', self.env.company.id)])

    # attribute master edit button
    def attribute_edit_open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Attribute',
            'res_model': 'product.attribute',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
            'context': {'no_breadcrumbs': True},
            'res_id': self.id,
        }

    def action_create_attribute_value(self):
        """Open wizard or form to create new attribute value"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Attribute Option',
            'res_model': 'product.attribute.value',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_attribute_id': self.id,
                'default_display_type': self.display_type,
            },
        }

    def action_create_sub_attribute(self):
        """Open wizard or form to create new sub-attribute for table"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Table Column',
            'res_model': 'product.attribute',  # or your sub-attribute model
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_attribute_id': self.id,
            },
        }

    # delete button attribute
    def attribute_master_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'attribute.master.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attribute_id': self.id},
        }

    def action_back_to_attribute_menu(self):
        menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    def sanitize_field_name(self, name):
        name = name.lower()
        name = name.replace(' #', '_1')
        name = name.replace('-', '')
        name = re.sub(r'[^a-z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        # Sanitize company name
        company_name = self.company_id.name or ''
        company_name = company_name.lower()
        company_name = re.sub(r'[^a-z0-9_]', '_', company_name)
        company_name = re.sub(r'_+', '_', company_name).strip('_')
        name = f'x_{name}_{company_name}'
        if not name[0].isalpha():
            name = 'x_' + name
        return name[:63]

    def get_create_vals(self, vals, model_id, d_type):
        """Create field vals as per attributes"""
        if d_type in ['select', 'color']:
            d_type = 'selection'
        elif d_type in ['text']:
            d_type = 'char'
        elif d_type in ['textarea']:
            d_type = 'text'
        elif d_type in ['date']:
            d_type = 'date'
        elif d_type in ['number']:
            d_type = 'float'
        elif d_type in ['float']:
            d_type = 'float'
        elif d_type in ['link', 'file', 'image']:
            d_type = 'binary'
        elif d_type in ['yes_no']:
            d_type = 'boolean'
        elif d_type in ['simple_select']:
            d_type = 'many2one'
        elif d_type in ['multi_select']:
            d_type = 'many2many'
        elif d_type in ['price']:
            d_type = 'monetary'
        elif d_type in ['table']:
            d_type = 'one2many'
        elif d_type in ['measurement']:
            d_type = 'float'

        base_vals = {
            'name': vals.original_name,
            'field_description': vals.name,
            'model_id': model_id.id,
            'state': 'manual'
        }

        if d_type in ['many2one']:
            base_vals.update({
                'ttype': d_type,
                'model': model_id.model,  # only required for backward compatibility
                'relation': 'product.attribute.value',
                'domain': '[("attribute_id", "=", %d)]' % vals.id,
            })
        # elif d_type in ['measurement']:
        #      uom_model_id = self.env['ir.model'].sudo().search([('model', '=', 'uom.uom')])
        #      base_vals.update({
        #           'model': uom_model_id.model,  # only required for backward compatibility
        #           'relation': 'uom.uom',
        #           'ttype': 'many2one',
        #      })
        elif d_type in ['many2many']:
            base_vals.update({
                'ttype': d_type,
                'model': model_id.model,  # only required for backward compatibility
                'relation': 'product.attribute.value',
                'relation_table': 'x_%s_rel' % vals.original_name.replace('.', '_'),
                'column1': 'attribute_id',
                'column2': '%s_id' % vals.original_name,
                'domain': '[("attribute_id", "=", %d)]' % vals.id,
            })
        elif d_type in ['one2many']:
            base_vals.update({
                'ttype': d_type,
                'model': model_id.model,  # only required for backward compatibility
                'relation': 'product.attribute',
                'relation_field': 'parent_attribute_id',
                #  'domain': '[("parent_attribute_id", "=", %d)]' % vals.id,
            })
        else:
            base_vals.update({
                'ttype': d_type,
            })
        if self.max_value and d_type in ['char']:
            base_vals.update({
                'size': self.max_value,
            })
        base_vals.update({'index': True})
        return base_vals

    def get_field_type(self, key):
        type_map = {
            "select": "selection", "color": "selection", "text": "char", "textarea": "text", "date": "date",
            "number": "float", "float": "float", "link": "binary", "file": "binary", "image": "binary",
            "yes_no": "boolean", "simple_select": "many2one", "multi_select": "many2many",
            "price": "monetary", "table": "one2many", "measurement": "float",
        }
        return type_map.get(key, "text")

    def standardize_field_name(self, name):
        """Standardize the field name as per odoo model field
        creation eg: with x_{{attribute_code}}_{{company_name}}"""
        sanitize = lambda s: re.sub(r'_+', '_',
                                    re.sub(r'[^a-z0-9_]', '_', s.lower().replace(' #', '_1').replace('-', ''))).strip(
            '_')
        base = sanitize(name)
        company = sanitize(self.company_id.name or '')
        full_name = f"x_{base}_{company}"
        return ('x_' + full_name if not full_name[0].isalpha() else full_name)[:63]

    def set_get_original_name(self):
        """Set original name if field is not set also return
        original name use standardization for field set"""
        if not self.original_name:
            self.original_name = self.standardize_field_name(self.code)
        return self.original_name

    def prepare_attribute_field_vals(self, model):
        """prepare the ir_field vals as per attribute conditions"""
        type_ = self.get_field_type(self.display_type)
        base_val = {
            'name': self.original_name,
            'field_description': self.name,
            'model_id': model.id,
            'state': 'manual',
            'ttype': type_,
            'required': self.is_mandatory or False,
            'copied': self.is_required_in_clone or False,
            'size': self.max_value or 0 if type_ == 'char' else 0
        }

        if type_ == 'many2one':
            base_val.update({
                'relation': 'product.attribute.value',
                'domain': f'[("attribute_id", "=", {self.id})]',
            })

        if type_ == 'many2many':
            base_val.update({
                'relation': 'product.attribute.value',
                'relation_table': f'x_{model.model.replace(".", "_")}_{self.original_name.replace(".", "_")}_rel',
                'column1': 'attribute_id',
                'column2': f'{model.model.replace(".", "_")}_{self.original_name}_id',
                'domain': f'[("attribute_id", "=", {self.id})]',
            })

        if type_ == 'one2many':
            base_val.update({
                'relation': 'product.attribute',
                'relation_field': 'parent_attribute_id',
            })

        if type_ == 'selection' and self.value_ids:
            base_val.update({
                'selection_ids': [
                    (0, 0, {
                        'name': x.name,
                        'value': x.html_color if self.display_type == 'color' else x.name,
                    }) for x in self.value_ids
                ]
            })

        # subfields creation
        if self.display_type in ['link', 'file', 'image']:
            sub_field = {
                'name': f'{self.original_name}_filename',
                'field_description': self.name,
                'model': model.model,
                'model_id': model.id,
                'ttype': 'char',
            }
            return base_val, sub_field

        if self.display_type == 'measurement':
            measure_field = {
                'name': f'{self.original_name}_mes',
                'field_description': f'{self.name} Unit',
                'model': model.model,
                'model_id': model.id,
                'ttype': 'selection',
                'selection_ids': [
                    (0, 0, {'name': x.name, 'value': x.name, }) for x in
                    self.value_ids
                ]
            }
            return base_val, measure_field

        return base_val, {}

    def create_attribute_field(self, model):
        """Create new attribute field in ir_fields as per display type"""
        self.ensure_one()
        ir_field = self.env['ir.model.fields'].sudo()
        try:
            base_val, sub_val = self.prepare_attribute_field_vals(model)
            self[f"{model.model.replace('.', '_')}_field_id"] = ir_field.create(
                base_val).id
            if sub_val:
                ir_field.create(sub_val)
            if self.display_type == 'table' and self.sub_attribute_ids:
                for rec in self.sub_attribute_ids:
                    rec.set_get_original_name()
                    sub_create_vals = rec.prepare_attribute_field_vals(model)
                    vals = [x for x in sub_create_vals if x]
                    ir_field.create(vals)
            return True
        except Exception as e:
            raise UserError(
                _(f"Error creating attribute fields for '{str(self.name)}': {str(e)}"))

    def update_attribute_field(self, model):
        """Update attribute field that exist"""
        self.ensure_one()
        if self.product_template_field_id:
            self.product_template_field_id.write({
                "field_description": self.name
            })
        if self.product_product_field_id:
            self.product_product_field_id.write({
                "field_description": self.name
            })

    def create_update_attribute_fields(self):
        """Create and update attribute fields"""
        product_models = self.env['ir.model'].sudo().search(
            [('model', 'in', ['product.template', 'product.product'])],
            order="id desc"
        )

        for rec in self:
            if rec.parent_id:
                continue

            rec.set_get_original_name()

            for model in product_models:
                field_ref = f"{model.model.replace('.', '_')}_field_id"

                if rec[field_ref]:
                    rec.update_attribute_field(model)
                else:
                    rec.create_attribute_field(model)

            if rec.is_usable_in_grid:
                self.create_product_list_view()

    def create_uncategorized_view(self):
        company_name = self.env.company.name
        attributes = self or self.env['product.attribute'].sudo().search(
            [('id', 'in', self.env.context['active_ids'])], order="id asc")
        widgets_mapping = {
            'image': 'image',
            'multi_select': 'many2many_tags',
            'color': 'pim_color',
            'price': 'monetary',
        }
        form_arch = ''
        for attr in attributes:
            field_tag = ''
            widget = widgets_mapping.get(attr.display_type)
            if attr.original_name and attr.display_type != 'table':
                field_tag += f'''\n<field name="{attr.original_name}" invisible="1"'''
                if attr.widget:
                    field_tag += f''' widget="{widget}"'''
                # if attr.usable_in_grid:
                #     field_tag += f''' optional="show"'''
                if attr.display_type in ['simple_select', 'multi_select']:
                    field_tag += f" options='{{\"no_create_edit\": True, \"no_edit\": True, \"no_open\": True}}'"

                field_tag += f'''/>\n'''
            form_arch += field_tag
        # Finding previous values
        last_attr = self.env['product.attribute'].search([("original_name", "!=", False)],
                                                         order="id desc", limit=1, offset=1)
        if len(last_attr) == 2:
            last_attr = last_attr[1]
        elif len(last_attr) == 1:
            last_attr = last_attr
        xpath_expr = f".//field[@name='{last_attr.original_name}']"

        default_view_id = self.env.ref('pim_ext.view_product_creation_split_view_custom').id
        view_name = 'product_attribute_' + company_name.lower().replace(' ', '_') + '_default'
        existing_view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.template')
        ], limit=1)

        if existing_view:
            exist_arch_tree = etree.fromstring(existing_view.arch_base)
            find_last_field = exist_arch_tree.find(xpath_expr)

            if find_last_field is not None:
                for field_str in form_arch.strip().split('\n'):
                    if field_str.strip():
                        field_elem = etree.fromstring(field_str.strip())
                        field_elem.tail = '\n    '
                        find_last_field.addnext(field_elem)
                etree.indent(exist_arch_tree, space="    ")
                updated_arch = etree.tostring(exist_arch_tree, pretty_print=True).decode()
                if updated_arch:
                    existing_view.write({'arch_base': updated_arch})
        else:
            view = self.env['ir.ui.view'].sudo().create({
                'name': view_name,
                'type': 'form',
                'model': 'product.template',
                'inherit_id': default_view_id,
                'active': True,
                'arch': """
                    <xpath expr="//notebook/page[@id='attributes_page']" position="inside">
                            <group name="default" string="Default" invisible="company_id not in [%s]" collapsible="1" expanded="1" >
                                                            %s
                                                     </group>
            </xpath>""" % (self.company_id.id, form_arch),
            })

    def _get_default_field_name(self):
        """
        Generate a safe, unique field name like x_att123_mycomp
        """
        self.ensure_one()
        if self.original_name:
            return self.original_name

        # Generate fallback name
        import re
        safe_name = re.sub(r'\W+', '_', self.name.lower()).strip('_')
        if not safe_name:
            safe_name = 'attr'

        # Add suffix to avoid conflict
        counter = 1
        field_name = f"x_{safe_name}"
        while self.env['ir.model.fields'].search([
            ('model', 'in', ['product.template', 'product.product']),
            ('name', '=', field_name)
        ]):
            field_name = f"x_{safe_name}_{counter}"
            counter += 1

        return field_name

    def create_product_list_view(self):
        """Add/Remove current attribute fields - ONE view per company per model"""
        from lxml import etree

        # Define both views separately
        view_configs = [
            {
                'model': 'product.template',
                'base_view_ref': 'pim_ext.view_product_management_tree',
                'view_name_prefix': 'pim_product_template_list_view'
            },
            {
                'model': 'product.product',
                'base_view_ref': 'pim_ext.view_product_product_management_tree',
                'view_name_prefix': 'pim_product_product_list_view'
            }
        ]

        for company in self.mapped('company_id'):
            company_suffix = company.name.lower().replace(' ', '_').replace('-',
                                                                            '_')

            # Get current attributes for this company
            current_attrs = self.filtered(
                lambda a: a.company_id == company and a.original_name)

            # Split into enabled and disabled
            enabled_attrs = current_attrs.filtered('is_usable_in_grid')
            disabled_attrs = current_attrs.filtered(
                lambda a: not a.is_usable_in_grid)

            for config in view_configs:
                view_name = f"{config['view_name_prefix']}_{company_suffix}"

                try:
                    base_view = self.env.ref(config['base_view_ref'])
                except:
                    continue

                # Search for existing inherited view
                inherited_view = self.env['ir.ui.view'].search([
                    ('name', '=', view_name),
                    ('model', '=', config['model']),
                    ('inherit_id', '=', base_view.id),
                ], limit=1)

                # === Handle ENABLED attributes (add to view) ===
                if enabled_attrs:
                    # Validate fields exist on this model
                    field_names = enabled_attrs.mapped('original_name')
                    existing = self.env['ir.model.fields'].sudo().search([
                        ('model', '=', config['model']),
                        ('name', 'in', field_names)
                    ]).mapped('name')
                    valid_attrs = enabled_attrs.filtered(
                        lambda a: a.original_name in existing)

                    if valid_attrs:
                        WIDGETS = {
                            'image': 'image',
                            'file': 'binary',
                            'multi_select': 'many2many_tags',
                            'color': 'pim_color',
                            'price': 'monetary',
                            'yes_no': 'boolean',
                            'date': 'date',
                        }

                        # Build field tags for enabled attributes
                        field_tags = []
                        for attr in valid_attrs:
                            tag = f'<field name="{attr.original_name}" optional="show"'
                            if WIDGETS.get(attr.display_type):
                                tag += f' widget="{WIDGETS[attr.display_type]}"'
                            if attr.display_type in ('simple_select',
                                                     'multi_select'):
                                tag += " options='{\"no_create\": true, \"no_open\": true}'"
                            tag += '/>'
                            field_tags.append(tag)

                        if inherited_view:
                            # === View exists - ADD new fields to existing xpath ===
                            try:
                                arch_tree = etree.fromstring(
                                    inherited_view.arch_base)
                                xpath_elem = arch_tree.find(
                                    ".//xpath[@expr=\"//button[@name='custom_product_open_form_view']\"]")

                                if xpath_elem is not None:
                                    # xpath exists - add fields inside it
                                    existing_fields = arch_tree.xpath(
                                        "//field/@name")

                                    for field_str in field_tags:
                                        field_elem = etree.fromstring(field_str)
                                        field_name = field_elem.get('name')

                                        if field_name not in existing_fields:
                                            field_elem.tail = '\n                '
                                            xpath_elem.append(field_elem)

                                    etree.indent(arch_tree, space="    ")
                                    updated_arch = etree.tostring(arch_tree,
                                                                  pretty_print=True).decode()
                                    inherited_view.write(
                                        {'arch_base': updated_arch})
                                else:
                                    # xpath doesn't exist but view exists - recreate entire view
                                    inherited_view.unlink()
                                    arch = f"""
                                        <xpath expr="//button[@name='custom_product_open_form_view']" position="before">
                                            {' '.join(field_tags)}
                                        </xpath>
                                    """
                                    self.env['ir.ui.view'].sudo().create({
                                        'name': view_name,
                                        'type': 'list',
                                        'model': config['model'],
                                        'inherit_id': base_view.id,
                                        'arch': arch,
                                        'active': True,
                                        'priority': 30,
                                    })
                            except Exception as e:
                                # If any error, recreate the view
                                if inherited_view.exists():
                                    inherited_view.unlink()
                                arch = f"""
                                    <xpath expr="//button[@name='custom_product_open_form_view']" position="before">
                                        {' '.join(field_tags)}
                                    </xpath>
                                """
                                self.env['ir.ui.view'].sudo().create({
                                    'name': view_name,
                                    'type': 'list',
                                    'model': config['model'],
                                    'inherit_id': base_view.id,
                                    'arch': arch,
                                    'active': True,
                                    'priority': 30,
                                })
                        else:
                            # === View doesn't exist - CREATE new view ===
                            arch = f"""
                                <xpath expr="//button[@name='custom_product_open_form_view']" position="before">
                                    {' '.join(field_tags)}
                                </xpath>
                            """

                            self.env['ir.ui.view'].sudo().create({
                                'name': view_name,
                                'type': 'list',
                                'model': config['model'],
                                'inherit_id': base_view.id,
                                'arch': arch,
                                'active': True,
                                'priority': 30,
                            })

                # === Handle DISABLED attributes (remove from view) ===
                if disabled_attrs and inherited_view:
                    try:
                        arch_tree = etree.fromstring(inherited_view.arch_base)
                        fields_to_remove = disabled_attrs.mapped(
                            'original_name')

                        # Remove disabled fields from view
                        for field_name in fields_to_remove:
                            field_nodes = arch_tree.xpath(
                                f"//field[@name='{field_name}']")
                            for node in field_nodes:
                                parent = node.getparent()
                                if parent is not None:
                                    parent.remove(node)

                        # Check if any fields remain
                        remaining_fields = arch_tree.xpath("//field")

                        if remaining_fields:
                            # Update view with remaining fields
                            etree.indent(arch_tree, space="    ")
                            updated_arch = etree.tostring(arch_tree,
                                                          pretty_print=True).decode()
                            inherited_view.write({'arch_base': updated_arch})
                        else:
                            # No fields left - delete the view
                            inherited_view.unlink()
                    except Exception as e:
                        # If error removing fields, just delete the view
                        if inherited_view.exists():
                            inherited_view.unlink()

    def create_pim_attribute_type(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Attribute',
            'res_model': 'pim.attribute.type',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
            'target': 'current',
            'context': {
                'default_is_create_mode': True,
                'default_master_attribute_ids': self.env['product.attribute'].search(
                    [('company_id', '=', self.env.company.id)]).ids,
            },
        }

    @api.constrains('name', 'code', 'value_ids')
    def check_attribute_name(self):
        pattern = "^(?=.*[a-zA-Z0-9])[A-Za-z0-9 ]+$"
        for rec in self:
            name_count = self.search_count([('code', '=ilike', rec.code), ('company_id', '=', rec.company_id.id)])
            if name_count > 1:
                raise ValidationError("Attribute code already exist")
            if rec.name and not re.match(pattern, rec.name):
                raise ValidationError("Attribute Name should be AlphaNumeric")

    def _log_changes(self, rec, vals, action):
        # Get the current time in UTC
        updated_write_date_utc = fields.Datetime.now()
        # Convert to the user's timezone
        user_tz = self.env.user.tz or 'UTC'  # Default to UTC if no timezone is set
        updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
        new_write_uid = self.env.user.display_name

        changes = []  # Store changes in list

        for key in vals:
            if key in ['name', 'code', 'active', 'create_variant', 'sequence', 'attribute_group',
                       'display_type', 'attribute_type_id', 'is_mandatory', 'is_required_in_clone',
                       'is_cloning', 'is_completeness', 'original_name', 'attribute_types',
                       'attribute_types_id', 'state', 'position_ref_field_id',
                       'unique_value', 'is_value_per_channel', 'is_value_per_locale', 'usable_in_grid',
                       'locale_specific', 'master_attribute_ids', 'label_transaltion', 'max_value',
                       'alpha_numeric_value']:

                attribute = rec._fields[key].string

                if key == 'attribute_group':
                    old_value = ', '.join(rec.attribute_group.mapped('display_name')) or 'N/A'
                    # Extract only the IDs from the command tuples (e.g., (4, id))
                    command_list = vals.get(key, [])
                    group_ids = []
                    for command in command_list:
                        if isinstance(command, (list, tuple)) and command[0] in [4, 6]:
                            if command[0] == 4:
                                group_ids.append(command[1])
                            elif command[0] == 6 and isinstance(command[1], list):
                                group_ids.extend(command[1])
                    new_value_recs = self.env['attribute.group'].browse(group_ids)
                    new_value = ', '.join(new_value_recs.mapped('display_name')) or 'N/A'
                # if key == 'attribute_group':
                #      old_value = rec.attribute_group.display_name if rec.attribute_group else 'N/A'
                #      new_value = self.env['attribute.group'].browse(vals[key]).display_name if vals.get(
                #           key) else 'N/A'
                else:
                    # Set old_value to 'N/A' if creating a new record
                    old_value = getattr(rec, key, 'N/A') if action == "update" else 'N/A'
                    new_value = vals[key] or 'N/A'

                # Formatting Old & New values on the same line with space
                change_entry = f"""
                  <li>
                      <strong>{attribute}</strong><br>
                      <span style='color: red;'>Old value:</span> {old_value}  
                      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                      <span style='color: green;'>New value:</span> {new_value}
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

    def set_get_default_group(self):
        """get default group if exist or create one"""
        group = self.env['attribute.group'].search(
            [('company_id', '=', self.company_id.id), ('name', '=ilike', 'Default')])
        if not group:
            group = self.env['attribute.group'].create({'name': 'Default',
                                                        'company_id': self.company_id.id})
        return group

    @api.model_create_multi
    def create(self, vals_list):
        """Create multiple attribute records with proper field and view generation"""
        # Generate codes
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code(
                    'pim.attribute.type') or '/'

        # Create records
        records = super(AttributeForm, self).create(vals_list)

        # Create dynamic fields for active records
        records.filtered('active').create_update_attribute_fields()

        # Assign default group and log
        default_group = records.set_get_default_group()
        for idx, rec in enumerate(records):
            rec._sync_attribute_groups_to_lines()
            rec.attribute_group = [(4, default_group.id)]
            rec._log_changes(rec, vals_list[idx], "create")

        return records

    def write(self, vals):
        """Supered the write method to dynamic changes on the fields"""
        # Track changes for table attributes
        table_rebuild_needed = set()
        color_value_changed = 'value_ids' in vals

        for rec in self:
            if rec.display_type == 'table':
                if 'sub_attribute_ids' in vals or 'original_name' in vals:
                    table_rebuild_needed.add(rec.id)

        # Log changes BEFORE write
        for rec in self:
            rec._log_changes(rec, vals, "update")

        # Perform the write
        result = super(AttributeForm, self).write(vals)

        # AFTER WRITE: Safe per-record processing
        for rec in self:
            # === COLOR ATTRIBUTE: Rebuild selection field if values changed ===
            if color_value_changed and rec.display_type == 'color' and rec.original_name:
                rec._update_color_selection_field()

            # Rebuild table line fields if needed
            if rec.id in table_rebuild_needed:
                rec._rebuild_table_line_fields()
                for model_name in ['product.template', 'product.product']:
                    model = self.env['ir.model'].search(
                        [('model', '=', model_name)], limit=1)
                    if model:
                        rec.create_attribute_field(model)

            # Sync group lines
            if "attribute_group" in vals and not self.env.context.get(
                    'from_group_line'):
                rec._sync_attribute_groups_to_lines()

            # Recreate fields if active or original_name changed
            if rec.active and rec.original_name:
                if (
                        'active' in vals or 'display_type' in vals or 'name' in vals):
                    rec.create_update_attribute_fields()

        # === Update grid view ONCE after all records processed ===
        if 'is_usable_in_grid' in vals:
            self.create_product_list_view()

        return result

    def _update_color_selection_field(self):
        """
        When color attribute values are changed → update the selection options
        on the dynamic field (x_att148_my_company) on product.template and product.product
        """
        self.ensure_one()
        if self.display_type != 'color' or not self.original_name:
            return

        field_name = self.original_name

        # Find the dynamic selection field on both models
        fields = self.env['ir.model.fields'].sudo().search([
            ('model', 'in', ['product.template', 'product.product']),
            ('name', '=', field_name),
            ('ttype', '=', 'selection'),
        ])

        if not fields:
            return

        # Build new selection values: [('value', 'Name'), ...]
        new_selection = [
            (v.html_color or '', v.name or '') for v in
            self.value_ids.sorted('sequence')
        ]

        # Remove empty ones
        new_selection = [(v, n) for v, n in new_selection if v and n]

        for field in fields:
            try:
                # Delete old selection lines
                field.selection_ids.unlink()

                # Create new ones
                if new_selection:
                    commands = [(0, 0, {'value': val, 'name': name}) for
                                val, name in new_selection]
                    field.write({'selection_ids': commands})

                _logger.info(
                    "Updated color selection field '%s' on %s with %d options",
                    field_name, field.model_id.model, len(new_selection))

            except Exception as e:
                _logger.warning("Failed to update color selection field %s: %s",
                                field_name, e)

    def _rebuild_table_line_fields(self):
        """
        Rebuild all dynamic fields on product.attribute.table.line for this table attribute
        Called when sub_attribute_ids change
        """
        self.ensure_one()
        if self.display_type != 'table':
            return

        table_model = self.env['ir.model'].search(
            [('model', '=', 'product.attribute.table.line')], limit=1)
        if not table_model:
            return

        ir_field = self.env['ir.model.fields'].sudo()

        # Get current field names on table line
        existing_fields = ir_field.search([
            ('model_id', '=', table_model.id),
            ('state', '=', 'manual')
        ]).mapped('name')

        for sub_attr in self.sub_attribute_ids.filtered('active'):
            sub_attr.set_get_original_name()
            desired_name = sub_attr.original_name

            # Skip if field already exists
            if desired_name in existing_fields:
                continue

            sub_type = sub_attr.get_field_type(sub_attr.display_type)

            safe_name = self._get_unique_field_name(
                'product.attribute.table.line', desired_name)

            field_vals = {
                'name': safe_name,
                'field_description': sub_attr.name,
                'model_id': table_model.id,
                'model': 'product.attribute.table.line',
                'ttype': sub_type,
                'state': 'manual',
                'index': True,
                'required': sub_attr.is_mandatory,
            }

            if sub_type in ['many2one', 'selection']:
                field_vals.update({
                    'relation': 'product.attribute.value',
                    'domain': f'[("attribute_id", "=", {sub_attr.id})]',
                })
            elif sub_type == 'many2many':
                rel_table = f"x_tbl_{safe_name}_rel"
                field_vals.update({
                    'relation': 'product.attribute.value',
                    'relation_table': rel_table,
                    'column1': 'table_line_id',
                    'column2': 'value_id',
                })
            elif sub_type == 'char' and sub_attr.max_value:
                field_vals['size'] = int(sub_attr.max_value or 0)

            try:
                ir_field.create(field_vals)
            except Exception as e:
                _logger.warning(
                    f"Failed to create table sub-field {safe_name}: {e}")

    def _update_list_view(self, company, mode='rebuild'):
        """
        Update product list view for a company.

        Args:
            company: Company record
            mode: 'add' = add fields from self
                  'remove' = remove fields from self
                  'update' = rebuild with all grid attributes
        """
        company_suffix = company.name.lower().replace(' ', '_').replace('-',
                                                                        '_')
        view_name = f"pim_product_list_view_columns_{company_suffix}"
        base_view = self.env.ref('pim_ext.view_product_management_tree')

        inherited_view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.template'),
            ('inherit_id', '=', base_view.id),
        ], limit=1)

        if mode == 'remove':
            # Remove ONLY the fields from self
            if not inherited_view:
                return

            try:
                arch = etree.fromstring(inherited_view.arch_db)
                modified = False

                for attr in self.filtered('original_name'):
                    for node in arch.xpath(
                            f"//field[@name='{attr.original_name}']"):
                        node.getparent().remove(node)
                        modified = True

                if modified:
                    # Check if any fields remain
                    remaining_fields = arch.xpath("//field")
                    if remaining_fields:
                        inherited_view.write({'arch_db': etree.tostring(arch,
                                                                        encoding='unicode')})
                    else:
                        # No fields left, delete the view
                        inherited_view.unlink()
            except Exception as e:
                _logger.warning(f"Failed to remove fields from list view: {e}")
            return

        # For 'add' and 'update' modes: get all grid attributes
        all_attrs = self.env['product.attribute'].search([
            ('company_id', '=', company.id),
            ('usable_in_grid', '=', 'yes'),
            ('original_name', '!=', False),
            ('active', '=', True)
        ])

        # Validate fields exist
        field_names = all_attrs.mapped('original_name')
        existing = self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'product.template'),
            ('name', 'in', field_names)
        ]).mapped('name')
        valid_attrs = all_attrs.filtered(lambda a: a.original_name in existing)

        if not valid_attrs:
            if inherited_view:
                inherited_view.unlink()
            return

        # Build field tags
        field_tags = []
        for attr in valid_attrs:
            tag = f'<field name="{attr.original_name}" string="{attr.name}" optional="show"'

            if attr.display_type in FIELD_WIDGETS:
                tag += f' widget="{FIELD_WIDGETS[attr.display_type]}"'

            if attr.display_type in ('simple_select', 'multi_select'):
                tag += ' options=\'{"no_create": true, "no_open": true}\''

            tag += '/>'
            field_tags.append(tag)

        arch = f"""
            <xpath expr="//button[@name='custom_product_open_form_view']" position="before">
                {' '.join(field_tags)}
            </xpath>
        """

        if inherited_view:
            inherited_view.write({'arch': arch})
        else:
            self.env['ir.ui.view'].sudo().create({
                'name': view_name,
                'type': 'list',
                'model': 'product.template',
                'inherit_id': base_view.id,
                'arch': arch,
                'active': True,
                'priority': 30,
            })

    def _sync_attribute_groups_to_lines(self):
        """Ensure attribute.group.lines reflect attribute_group exactly"""
        for rec in self:
            # Current groups on product.attribute
            current_groups = set(rec.attribute_group.ids)

            # All existing lines for this attribute
            existing_lines = self.env['attribute.group.lines'].search([
                ('product_attribute_id', '=', rec.id)
            ])
            existing_groups = set(existing_lines.mapped('attr_group_id').ids)

            # Groups to remove (lines exist but not in current_groups)
            groups_to_remove = existing_groups - current_groups
            if groups_to_remove:
                existing_lines.filtered(
                    lambda l: l.attr_group_id.id in groups_to_remove).unlink()

            # Groups to add (missing lines)
            groups_to_add = current_groups - existing_groups
            for gid in groups_to_add:
                self.env['attribute.group.lines'].create({
                    'attr_group_id': gid,
                    'product_attribute_id': rec.id,
                })

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
                record_name = self.env['product.attribute.value'].search([('html_color', '=', color),
                                                                          ('attribute_id', '=', record.id)],
                                                                         order="id", limit=1)
                vals_list.append((0, 0, {
                    'name': record_name.name,
                    'html_color': color,
                    'attribute_id': record.id,
                    'image': record_name.image
                }))
            record.value_ids.unlink()
            record.value_ids = vals_list

    def remove_attributes_from_view(self):
        attr = self or self.env['product.attribute'].sudo().search(
            [('id', 'in', self.env.context['active_ids'])], order="id asc")
        for rec in attr:
            # if rec.display_type in ['link', 'file', 'image'] and rec.original_name:
            #     field_file_name = rec.original_name + '_file_name'
            #     field_val_binary = self.env['ir.model.fields'].sudo().search([('name', '=ilike', field_file_name)])
            #     field_val_binary.unlink()

            extra_view_ids = []
            list_view_ids = []
            attribute_groups = self.env['attribute.group.lines'].search(
                [('product_attribute_id', '=', rec.id)])
            if attribute_groups:
                for group in attribute_groups:
                    company_name = group.attr_group_id.company_id.name
                    group_name = group.attr_group_id.name
                    if group.attr_group_id:
                        view_name = f"product_attribute_{company_name.lower().replace(' ', '_')}_{group_name.lower().replace(' ', '_')}"
                        attribute_group_views = self.env['ir.ui.view'].sudo().search(
                            [('name', '=', view_name), ('active', 'in', [True, False])])
                        if attribute_group_views:
                            extra_view_ids.append(attribute_group_views)
            # Uncategorized Group View
            companies = self.env['res.company'].search([])
            for com in companies:
                name = com.name
                com_view_name = 'product_attribute_' + name.lower().replace(' ', '_') + '_default'
                company_views = self.env['ir.ui.view'].sudo().search(
                    [('name', '=', com_view_name), ('active', 'in', [True, False])])
                if company_views:
                    extra_view_ids.append(company_views)
                list_view_name = 'product_attribute_list_view' + name.lower().replace(' ', '_')
                company_list_views = self.env['ir.ui.view'].sudo().search(
                    [('name', '=', list_view_name), ('active', 'in', [True, False])])
                if company_list_views:
                    list_view_ids.append(company_list_views)
            if extra_view_ids:
                for view in extra_view_ids:
                    if view:
                        arch_tree = etree.fromstring(view.arch_db)
                        # Define field names to remove
                        fields_to_remove = [rec.original_name]
                        # if rec.display_type == 'link':
                        #     field_file_name = f"{rec.original_name}_file_name"
                        #     fields_to_remove.append(field_file_name)
                        for field_name in fields_to_remove:
                            # Find the field node
                            field_node = arch_tree.xpath(f"//field[@name='{field_name}']")
                            if field_node:
                                # Remove the field node
                                parent_node = field_node[0].getparent()
                                parent_node.remove(field_node[0])

                        # Save the modified XML back to the view
                        view.write({'arch_db': etree.tostring(arch_tree, encoding='utf-8').decode('utf-8')})
            if list_view_ids:
                for view in list_view_ids:
                    if view:
                        arch_tree = etree.fromstring(view.arch_db)
                        fields_to_remove = [rec.original_name]
                        for field_name in fields_to_remove:
                            field_node = arch_tree.xpath(f"//field[@name='{field_name}']")
                            if field_node:
                                parent_node = field_node[0].getparent()
                                parent_node.remove(field_node[0])

                        # Save the modified XML back to the view
                        view.write({'arch_db': etree.tostring(arch_tree, encoding='utf-8').decode('utf-8')})

            if rec.original_name:
                field_val = self.env['ir.model.fields'].sudo().search(
                    [('name', '=ilike', rec.original_name), ('model', '=', 'product.template')])
                field_val.unlink()

    def unlink(self):
        """
        Delete attribute records with COMPLETE cleanup
        in the correct order.
        """
        if not self:
            return True

        families_to_rebuild = self.env['family.attribute']
        family_attr_lines_to_delete = self.env['family.attributes'].search([
            ('attribute_id', 'in', self.ids)
        ])
        if family_attr_lines_to_delete:
            families_to_rebuild = family_attr_lines_to_delete.mapped('family_id')

        field_names_to_delete = []
        channel_fields_to_delete = self.env['ir.model.fields']

        for attr in self.filtered('original_name'):
            field_name = attr.original_name
            field_names_to_delete.append(field_name)

            if attr.display_type in ('image', 'file', 'link'):
                field_names_to_delete.append(f"{field_name}_file_name")
            if attr.display_type == 'measurement':
                field_names_to_delete.append(f"{field_name}_mes")
            # if attr.channel_field_id:
            # field_names_to_delete.append(attr.channel_field_id.name)
            # channel_fields_to_delete |= attr.channel_field_id

        if family_attr_lines_to_delete:
            family_attr_lines_to_delete.unlink()

        if channel_fields_to_delete:
            channel_fields_to_delete.unlink()

        result = super(AttributeForm, self).unlink()

        if result:
            for family in families_to_rebuild.exists():
                if family.family_sequence_id:
                    family.update_view_in_sequence()

            if field_names_to_delete:
                all_views = self.env['ir.ui.view'].search([
                    ('model', 'in', ['product.template', 'product.product'])
                ])
                for view in all_views:
                    try:
                        arch = etree.fromstring(view.arch_db)
                        modified = False
                        for field_name in field_names_to_delete:
                            nodes = arch.xpath(f"//field[@name='{field_name}']")
                            if nodes:
                                modified = True
                                for node in nodes:
                                    node.getparent().remove(node)
                        if modified:
                            view.write({'arch_db': etree.tostring(arch, encoding='unicode')})
                    except Exception as e:
                        _logger.warning(f"Could not clean view {view.id} ({view.name}): {e}")

            if field_names_to_delete:
                fields_to_delete = self.env['ir.model.fields'].sudo().search([
                    ('model', 'in', ['product.template', 'product.product']),
                    ('name', 'in', field_names_to_delete)
                ])
                if fields_to_delete:
                    try:
                        fields_to_delete.unlink()
                    except Exception as e:
                        _logger.error(f"Error deleting ir.model.fields: {e}")

            self.env['ir.ui.view'].invalidate_model(['arch_db'])
            self.env['ir.model.fields'].invalidate_model()

        return result


    def _rebuild_list_view(self, company):
        """
        Rebuild product list view for a specific company with all usable_in_grid attributes.

        This method:
        - Gets all active attributes with usable_in_grid='yes' for the company
        - Validates fields exist in ir.model.fields
        - Builds field tags with proper widgets and options
        - Creates or updates the inherited list view

        Args:
            company (res.company): Company record to rebuild view for
        """
        company_suffix = company.name.lower().replace(' ', '_').replace('-',
                                                                        '_')
        view_name = f"pim_product_list_view_columns_{company_suffix}"
        base_view = self.env.ref('pim_ext.view_product_management_tree')

        # Find existing inherited view
        inherited_view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.template'),
            ('inherit_id', '=', base_view.id),
        ], limit=1)

        # Get all grid attributes for this company
        all_attrs = self.env['product.attribute'].search([
            ('company_id', '=', company.id),
            ('usable_in_grid', '=', 'yes'),
            ('original_name', '!=', False),
            ('active', '=', True)
        ])

        # Validate fields exist
        field_names = all_attrs.mapped('original_name')
        existing = self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'product.template'),
            ('name', 'in', field_names)
        ]).mapped('name')
        valid_attrs = all_attrs.filtered(lambda a: a.original_name in existing)

        if not valid_attrs:
            if inherited_view:
                inherited_view.unlink()
            return

        # Build field tags
        field_tags = []
        for attr in valid_attrs:
            tag = f'<field name="{attr.original_name}" string="{attr.name}" optional="show"'

            # Add widget
            if attr.display_type in FIELD_WIDGETS:
                tag += f' widget="{FIELD_WIDGETS[attr.display_type]}"'

            # Add options for select fields
            if attr.display_type in ('simple_select', 'multi_select'):
                tag += ' options=\'{"no_create": true, "no_open": true}\''

            tag += '/>'
            field_tags.append(tag)

        # Build arch
        arch = f"""
            <xpath expr="//button[@name='custom_product_open_form_view']" position="before">
                {' '.join(field_tags)}
            </xpath>
        """

        # Create or update view
        if inherited_view:
            inherited_view.write({'arch': arch})
        else:
            self.env['ir.ui.view'].sudo().create({
                'name': view_name,
                'type': 'list',
                'model': 'product.template',
                'inherit_id': base_view.id,
                'arch': arch,
                'active': True,
                'priority': 30,
            })

    def _remove_list_view(self, company):
        """
        Remove product list view for a specific company.

        Args:
            company (res.company): Company record to remove view for
        """
        company_suffix = company.name.lower().replace(' ', '_').replace('-',
                                                                        '_')
        view_name = f"pim_product_list_view_columns_{company_suffix}"

        inherited_view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.template'),
        ], limit=1)

        if inherited_view:
            inherited_view.unlink()

    def create_product_list_view(self):
        """
        Backwards compatible method - rebuilds list view for all companies in recordset.

        This method maintains compatibility with existing code that calls
        create_product_list_view() directly.
        """
        for company in self.mapped('company_id'):
            self._rebuild_list_view(company)


class AttributeMasterUnlinkWizard(models.TransientModel):
    _name = 'attribute.master.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Attribute master'

    attribute_id = fields.Many2one('product.attribute', string="Attribute Master")

    def confirm_unlink(self):
        if self.attribute_id:
            self.attribute_id.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.depends('attribute_id')
    def _compute_display_name(self):
        for value in self:
            value.display_name = f"{value.name}"
