import time, pytz, re, json
from datetime import datetime
from lxml import etree
from odoo import models, api, fields, _, tools
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProductBrand(models.Model):
    _name = 'product.brand'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Brand Management'
    _rec_name = 'name'
    _order = 'create_date desc'

    # ==================== CORE BRAND FIELDS ====================
    code = fields.Char(string="Code", readonly=True, copy=False, tracking=True)
    name = fields.Char('Brand Name', required=True, translate=True, tracking=True)
    is_mandatory = fields.Boolean(string="Mandatory on Brand", default=False, tracking=True)
    description = fields.Text('Description', translate=True, tracking=True)

    # Image fields
    image_1920 = fields.Image("Brand Logo", max_width=1920, max_height=1920)
    avatar_128 = fields.Image("Avatar", related='image_1920', max_width=128, max_height=128, store=True)
    brand_logo = fields.Image(related='image_1920', string="Brand Logo", readonly=False, store=True)

    website = fields.Char("Website URL", tracking=True)
    company_id = fields.Many2one('res.company', required=True, readonly=False,
                                 default=lambda self: self.env.company, tracking=True)
    tagline = fields.Char('Tagline', translate=True, tracking=True)
    country_of_origin = fields.Many2one('res.country', string='Country of Origin', tracking=True)

    seo_title = fields.Char('SEO Title', translate=True, tracking=True)
    seo_description = fields.Text('SEO Description', translate=True, tracking=True)
    seo_keywords = fields.Char('SEO Keywords', translate=True, tracking=True)

    brand_attribute_ids = fields.One2many('brand.attributes', 'brand_id', 'Brand Attributes', tracking=True)
    exist_attribute_ids = fields.Many2many('product.brand.attribute', 'brand_mapped_attributes_rel',
                                           'brand_id', 'attribute_id', string='Exist Attributes',
                                           compute='_compute_exist_relations', store=True)
    exist_group_ids = fields.Many2many('product.brand.attribute.group', 'brand_mapped_groups_rel',
                                       'brand_id', 'attribute_group_id', string='Exist Attribute Groups',
                                       compute='_compute_exist_relations', store=True)
    brand_sequence_id = fields.Many2one('brand.attribute.sequence', readonly=True)

    dynamic_properties = fields.Json(string='Dynamic Properties', default=dict)

    completeness = fields.Float(string='Profile Completeness (%)', compute='_compute_completeness',
                                store=True, group_operator="avg")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id,
                                  required=True, tracking=True)
    product_count = fields.Integer(compute="_compute_product_count", store=True, string="Products")
    history_log = fields.Html(string='History Log', readonly=True)
    is_create_mode = fields.Boolean(default=False, string='Create Mode')
    master_brand_ids = fields.Many2many('product.brand', 'product_brand_master_rel',
                                        'current_brand_id', 'master_brand_id', string='Brands',
                                        compute='_compute_master_brand_ids', store=False)
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user, tracking=True)
    attribute_label = fields.Char(string='Translation')

    # ==================== CLEANUP & FETCH OVERRIDES ====================
    def _cleanup_invalid_dynamic_views(self):
        View = self.env['ir.ui.view'].sudo()
        views = View.search([('model', '=', 'product.brand'), ('name', 'like', 'product_brand_dynamic_%')])
        valid_fields = set(self.fields_get().keys())

        for view in views:
            arch = view.arch or ''
            invalid = False
            for field_name in re.findall(r'name="(x_[a-z0-9_]+)"', arch):
                if field_name not in valid_fields:
                    invalid = True
                    break
            if invalid:
                _logger.warning(f"Deleting stale dynamic view {view.name}")
                view.unlink()

    def fetch(self, field_names):
        """Filter out dynamic fields from ORM fetch"""
        standard_fields = [f for f in field_names if f in self._fields or not str(f).startswith('x_')]
        super().fetch(standard_fields)

    def onchange(self, values, field_name, field_onchange):
        """Filter dynamic fields from onchange"""
        safe_values = {k: v for k, v in values.items() if not str(k).startswith('x_') or k in self._fields}
        safe_onchange = {k: v for k, v in (field_onchange or {}).items() if
                         not str(k).startswith('x_') or k in self._fields}
        return super().onchange(safe_values, field_name, safe_onchange)

    # ==================== WRITE WITH COMPREHENSIVE LOGGING ====================
    def write(self, vals):
        """Override write to track ALL field changes + regenerate view when attributes change"""
        if not self.env.context.get('skip_history_log'):
            for rec in self:
                rec._log_changes_enhanced(vals, "update")

        dynamic = {k: v for k, v in vals.items() if k.startswith('x_')}
        static = {k: v for k, v in vals.items() if not k.startswith('x_')}

        result = super().write(static)

        if dynamic:
            for rec in self:
                props = rec.dynamic_properties or {}
                if isinstance(props, str):
                    try:
                        props = json.loads(props)
                    except:
                        props = {}
                old_props = props.copy()
                props.update(dynamic)
                if not self.env.context.get('skip_history_log'):
                    rec._log_dynamic_changes(old_props, props)
                super(ProductBrand, rec).write({'dynamic_properties': props})

        if 'brand_attribute_ids' in vals:
            for rec in self:
                rec._regenerate_brand_view()

        return result

    # ==================== ENHANCED LOGGING METHODS ====================
    def _log_changes_enhanced(self, vals, action):
        """Enhanced logging using UL/LI list structure"""
        if self.env.context.get('skip_history_log'):
            return

        self.ensure_one()
        user_tz = self.env.user.tz or 'UTC'
        try:
            local_dt = fields.Datetime.now().astimezone(pytz.timezone(user_tz))
        except Exception:
            local_dt = fields.Datetime.now()
        updated_write_date = local_dt.strftime("%d/%m/%Y %H:%M:%S")
        user_name = self.env.user.display_name
        list_items = []

        # Track normal fields
        tracked_fields = ['name', 'description', 'tagline', 'website', 'company_id',
                          'country_of_origin', 'seo_title', 'seo_description',
                          'seo_keywords', 'currency_id', 'user_id', 'is_mandatory']

        for key in vals:
            if key in tracked_fields and key in self._fields:
                field = self._fields[key]
                field_label = field.string or key
                old_value = getattr(self, key, 'N/A') if action == "update" else 'N/A'
                new_value = vals.get(key)

                if isinstance(field, fields.Many2one):
                    old_value = old_value.display_name if hasattr(old_value, 'display_name') else (old_value or 'N/A')
                    new_value = self.env[field.comodel_name].browse(new_value).display_name if new_value else 'N/A'
                elif isinstance(field, fields.Boolean):
                    old_value = "Yes" if old_value else "No"
                    new_value = "Yes" if new_value else "No"
                else:
                    old_value = old_value if old_value not in (False, None, '') else 'N/A'
                    new_value = new_value if new_value not in (False, None, '') else 'N/A'

                if str(old_value) != str(new_value) or action == "create":
                    list_items.append(f"""
                        <li style="margin-bottom: 10px; list-style-type: none;">
                            <strong>{field_label}</strong><br/>
                            <span style="color: #dc3545;">Old value:</span> {old_value}
                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                            <span style="color: #28a745;">New value:</span> {new_value}
                        </li>
                    """)

        # Track One2many fields
        tracked_one2many_fields = {'brand_attribute_ids': ['attribute_id', 'is_visible']}

        for field_name, subfields in tracked_one2many_fields.items():
            if field_name not in vals or field_name not in self._fields:
                continue
            parent_label = self._fields[field_name].string

            for command in vals[field_name]:
                if command[0] == 1:  # UPDATE
                    line = self[field_name].browse(command[1])
                    for sub in subfields:
                        if sub in command[2]:
                            subfield = line._fields[sub]
                            old_val = getattr(line, sub, 'N/A')
                            new_val = command[2][sub]
                            if isinstance(subfield, fields.Many2one):
                                old_val = old_val.display_name if old_val else 'N/A'
                                new_val = self.env[subfield.comodel_name].browse(
                                    new_val).display_name if new_val else 'N/A'
                            list_items.append(f"""
                                <li style="margin-bottom: 10px; list-style-type: none;">
                                    <strong>{subfield.string}</strong> <small>(in {parent_label})</small><br/>
                                    <span style="color: #dc3545;">Old value:</span> {old_val}
                                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                    <span style="color: #28a745;">New value:</span> {new_val}
                                </li>
                            """)
                elif command[0] == 0:  # CREATE
                    for sub in subfields:
                        if sub in command[2]:
                            subfield = self.env[self._fields[field_name].comodel_name]._fields[sub]
                            new_val = command[2][sub]
                            if isinstance(subfield, fields.Many2one):
                                new_val = self.env[subfield.comodel_name].browse(
                                    new_val).display_name if new_val else 'N/A'
                            list_items.append(f"""
                                <li style="margin-bottom: 10px; list-style-type: none;">
                                    <strong>{subfield.string}</strong> <small>(Added to {parent_label})</small><br/>
                                    <span style="color: #dc3545;">Old value:</span> N/A
                                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                    <span style="color: #28a745;">New value:</span> {new_val}
                                </li>
                            """)
                elif command[0] == 2:  # DELETE
                    line = self[field_name].browse(command[1])
                    if line.exists():
                        primary_sub = subfields[0]
                        old_val = getattr(line, primary_sub, 'N/A')
                        if hasattr(line._fields[primary_sub], 'display_name'):
                            old_val = old_val.display_name if old_val else 'N/A'
                        list_items.append(f"""
                            <li style="margin-bottom: 10px; list-style-type: none;">
                                <strong>{parent_label}</strong> <small>(Removed Item)</small><br/>
                                <span style="color: #dc3545;">Old value:</span> {old_val}
                                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                <span style="color: #28a745;">New value:</span> N/A
                            </li>
                        """)

        if list_items:
            action_text = "Created" if action == "create" else "Updated"
            msg = f"""
            <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                <small style="color: #6c757d;">{action_text} by <strong>{user_name}</strong> on {updated_write_date}</small>
                <ul style="list-style-type: none; padding-left: 0; margin-top: 8px;">
                    {''.join(list_items)}
                </ul>
            </div>
            """
            self.history_log = tools.html_sanitize(msg) + (self.history_log or '')

    def _log_dynamic_changes(self, old_props, new_props):
        """Log changes to dynamic properties (x_ fields) with table format"""
        if self.env.context.get('skip_history_log'):
            return

        user_tz = self.env.user.tz or 'UTC'
        updated = fields.Datetime.now().astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
        user = self.env.user.display_name
        changes = []

        all_keys = set(old_props.keys()) | set(new_props.keys())
        for key in all_keys:
            old_val = old_props.get(key)
            new_val = new_props.get(key)
            if old_val != new_val:
                attr = self.env['product.brand.attribute'].search([('original_name', '=', key)], limit=1)
                field_label = attr.name if attr else key.replace('x_', '').replace('_', ' ').title()
                old_display = self._format_dynamic_value(old_val) if old_val else 'N/A'
                new_display = self._format_dynamic_value(new_val) if new_val else 'N/A'
                changes.append({'field': field_label, 'old': old_display, 'new': new_display})

        if changes:
            table_rows = []
            for change in changes:
                table_rows.append(f"""
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e9ecef; font-weight: 600; color: #495057; width: 30%;">
                            {change['field']}
                        </td>
                        <td style="padding: 8px; border-bottom: 1px solid #e9ecef; color: #6c757d; width: 35%;">
                            <span style='color: red;'>Old value:</span> {change['old']}
                        </td>
                        <td style="padding: 8px; border-bottom: 1px solid #e9ecef; color: #28a745; width: 35%;">
                            <span style='color: green;'>New value:</span> {change['new']}
                        </td>
                    </tr>
                """)
            msg = f"""
            <div style="border-left: 3px solid #17a2b8; padding-left: 10px; margin-bottom: 15px;">
                <small>Attribute Values Updated by {user} on {updated}</small>
                <ul style="list-style-type: none; padding-left: 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tbody>{''.join(table_rows)}</tbody>
                    </table>
                </ul>
            </div>
            """
            self.history_log = tools.html_sanitize(msg) + (self.history_log or '')

    def _format_dynamic_value(self, value):
        """Format dynamic field value for display"""
        if value is None or value == '':
            return 'N/A'
        if isinstance(value, bool):
            return 'Yes' if value else 'No'
        if isinstance(value, (list, tuple)):
            return ', '.join(str(v) for v in value)
        if isinstance(value, str) and len(value) == 10 and value.count('-') == 2:
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt.strftime('%d/%m/%Y')
            except:
                pass
        return str(value)

    # ==================== CREATE WITH LOGGING ====================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('product.brand.sequence') or 'BRAND-NEW'

            dynamic_data = {}
            keys_to_remove = []
            for k, v in vals.items():
                if k.startswith('x_'):
                    dynamic_data[k] = v
                    keys_to_remove.append(k)

            if dynamic_data:
                raw_props = vals.get('dynamic_properties')
                if not raw_props:
                    current_props = {}
                elif isinstance(raw_props, str):
                    try:
                        current_props = json.loads(raw_props)
                    except ValueError:
                        current_props = {}
                elif isinstance(raw_props, dict):
                    current_props = raw_props
                else:
                    current_props = {}
                current_props.update(dynamic_data)
                vals['dynamic_properties'] = current_props

            for k in keys_to_remove:
                del vals[k]

        records = super().create(vals_list)

        for idx, rec in enumerate(records):
            log_vals = vals_list[idx].copy()
            if rec.dynamic_properties:
                props = rec.dynamic_properties
                if isinstance(props, str):
                    try:
                        props = json.loads(props)
                    except:
                        props = {}
                if isinstance(props, dict):
                    log_vals.update(props)
            if not self.env.context.get('skip_history_log'):
                rec._log_changes_enhanced(log_vals, "create")
            if rec.brand_attribute_ids:
                rec._regenerate_brand_view()

        return records

    # ==================== UNLINK WITH CONFIRMATION ====================
    def unlink(self):
        """Delete with confirmation if products exist"""
        if self.env.context.get('allow_force_delete'):
            for brand in self:
                affected = self.env['product.template'].search([('brand_id', 'in', self.ids)])
            result = super().unlink()
            if affected and result:
                affected.with_context(skip_history_log=True).write({'brand_id': False})
            return result

        for brand in self:
            if brand.product_count > 0:
                return {
                    'name': 'Confirm Deletion',
                    'type': 'ir.actions.act_window',
                    'res_model': 'brand.delete.confirmation.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_brand_id': brand.id},
                }
        return super().unlink()

    # ==================== VIEW REGENERATION ====================
    def _regenerate_brand_view(self):
        self.ensure_one()
        view_name = f"product_brand_dynamic_{self.id}"
        existing_view = self.env['ir.ui.view'].sudo().search([
            ('name', '=', view_name), ('model', '=', 'product.brand')
        ], limit=1)

        if existing_view:
            existing_view.unlink()

        visible_attrs = self.brand_attribute_ids.filtered(lambda a: a.is_visible)
        if not visible_attrs:
            return

        arch_lines = ['<?xml version="1.0"?>', '<data>']
        visible_groups = visible_attrs.mapped('attribute_group_id')

        if self.brand_sequence_id and self.brand_sequence_id.attr_group_ids:
            seq_lines = self.brand_sequence_id.attr_group_ids.sorted('sequence')
            groups = [l.attribute_group_id for l in seq_lines if l.attribute_group_id in visible_groups]
            for g in visible_groups:
                if g not in groups:
                    groups.append(g)
        else:
            groups = list(visible_groups.sorted('sequence'))

        system_groups = []
        custom_groups = []

        for grp in groups:
            grp_attrs = visible_attrs.filtered(lambda l: l.attribute_group_id.id == grp.id).sorted(
                lambda l: l.attribute_id.sequence)
            if not grp_attrs:
                continue

            is_system = False
            xpath_target = None
            system_group_xpaths = {
                'basic_info': "//group[@name='group_basic_info']",
                'description': "//group[@name='group_description']",
                'seo': "//group[@name='group_seo']",
            }

            if hasattr(grp, 'technical_name') and grp.technical_name in system_group_xpaths:
                is_system = True
                xpath_target = system_group_xpaths[grp.technical_name]
            else:
                name_to_xpath = {
                    'Basic Information': "//group[@name='group_basic_info']",
                    'Description': "//group[@name='group_description']",
                    'SEO Metadata': "//group[@name='group_seo']",
                }
                if grp.name in name_to_xpath:
                    is_system = True
                    xpath_target = name_to_xpath[grp.name]

            if is_system and xpath_target:
                system_groups.append((grp, grp_attrs, xpath_target))
            else:
                custom_groups.append((grp, grp_attrs))

        for grp, grp_attrs, xpath_target in system_groups:
            arch_lines.append(f'  <xpath expr="{xpath_target}" position="inside">')
            arch_lines.append('    <group>')
            for line in grp_attrs:
                attr = line.attribute_id
                field_name = attr.original_name
                if not field_name or not field_name.startswith('x_') or field_name not in self.fields_get():
                    continue
                widget, options = self._get_field_widget_options(attr)
                from xml.sax.saxutils import escape
                label = escape(attr.name or field_name)
                field_tag = f'      <field name="{field_name}" string="{label}"'
                if widget:
                    field_tag += widget
                if options:
                    field_tag += options
                field_tag += '/>'
                arch_lines.append(field_tag)
            arch_lines.append('    </group>')
            arch_lines.append('  </xpath>')

        if custom_groups:
            arch_lines.append(f'  <xpath expr="//page[@name=\'Properties\']" position="inside">')
            arch_lines.append(f'    <group name="dynamic_attrs_brand_{self.id}" invisible="id != {self.id}">')
            for grp, grp_attrs in custom_groups:
                from xml.sax.saxutils import escape
                group_label = escape(grp.name or 'Attributes')
                arch_lines.append(f'      <separator string="{group_label}" colspan="2"/>')
                arch_lines.append(f'      <group name="dynamic_grp_{grp.id}_brand_{self.id}" col="2" colspan="2">')
                for line in grp_attrs:
                    attr = line.attribute_id
                    field_name = attr.original_name
                    if not field_name or not field_name.startswith('x_'):
                        continue
                    widget, options = self._get_field_widget_options(attr)
                    label = escape(attr.name or field_name)
                    field_tag = f'        <field name="{field_name}" string="{label}"'
                    if widget:
                        field_tag += widget
                    if options:
                        field_tag += options
                    field_tag += '/>'
                    arch_lines.append(field_tag)
                arch_lines.append('      </group>')
            arch_lines.append('    </group>')
            arch_lines.append('  </xpath>')

        arch_lines.append('</data>')
        arch_xml = '\n'.join(arch_lines)

        try:
            etree.fromstring(arch_xml)
        except Exception as e:
            raise ValidationError(f"Failed to generate valid view XML: {e}")

        base_view = self.env.ref('pim_ext.view_product_brand_split_view_custom')
        self.env['ir.ui.view'].sudo().create({
            'name': view_name,
            'model': 'product.brand',
            'inherit_id': base_view.id,
            'mode': 'extension',
            'arch': arch_xml,
            'priority': 1000,
            'active': True,
        })

        self.env['ir.ui.view'].clear_caches()
        self.env.registry.clear_cache()
        self._cleanup_invalid_dynamic_views()

    def _get_field_widget_options(self, attr):
        """Helper to get widget and options for a field"""
        widget_map = {
            'image': ('image', "{'size': [128, 128]}"),
            'color': ('color', ''),
            'price': ('monetary', "{'currency_field': 'currency_id'}"),
            'file': ('binary', ''),
            'textarea': ('text', ''),
            'date': ('date', ''),
            'boolean': ('boolean_toggle', ''),
        }
        if attr.display_type in widget_map:
            w, o = widget_map[attr.display_type]
            widget = f' widget="{w}"' if w else ''
            options = f' options="{o}"' if o else ''
            return widget, options
        return '', ''

    # ==================== COMPUTED FIELDS ====================
    @api.depends('brand_attribute_ids', 'brand_attribute_ids.attribute_id',
                 'brand_attribute_ids.attribute_group_id')
    def _compute_exist_relations(self):
        for rec in self:
            rec.exist_attribute_ids = rec.brand_attribute_ids.mapped('attribute_id')
            rec.exist_group_ids = rec.brand_attribute_ids.mapped('attribute_group_id')

    @api.depends_context('company')
    def _compute_master_brand_ids(self):
        for record in self:
            record.master_brand_ids = self.env['product.brand'].search([
                ('company_id', '=', self.env.company.id)
            ], order='create_date desc')

    @api.depends('name', 'brand_logo', 'website', 'description', 'tagline',
                 'country_of_origin', 'seo_title', 'seo_description', 'seo_keywords',
                 'brand_attribute_ids', 'dynamic_properties')
    def _compute_completeness(self):
        for rec in self:
            core = ['name', 'brand_logo', 'description', 'website', 'tagline', 'country_of_origin']
            filled = sum(1 for f in core if getattr(rec, f, False))
            if rec.brand_attribute_ids:
                total = len(core) + len(rec.brand_attribute_ids)
                props = rec.dynamic_properties or {}
                if isinstance(props, str):
                    props = json.loads(props) if props else {}
                for attr_line in rec.brand_attribute_ids:
                    if props.get(attr_line.attribute_id.original_name):
                        filled += 1
            else:
                total = len(core)
            rec.completeness = (filled / total * 100) if total > 0 else 0.0

    @api.depends('name')
    def _compute_product_count(self):
        for rec in self:
            rec.product_count = self.env['product.template'].search_count([('brand_id', '=', rec.id)])

    # ==================== FIELDS GET ====================
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Register all x_ fields so Odoo recognizes them"""
        res = super().fields_get(allfields, attributes)
        all_attrs = self.env['product.brand.attribute'].sudo().search([
            ('original_name', '!=', False), ('original_name', '=like', 'x_%')
        ])
        type_map = {
            'textarea': 'text', 'image': 'binary', 'file': 'binary', 'boolean': 'boolean',
            'integer': 'integer', 'float': 'float', 'price': 'float', 'date': 'date',
        }
        for attr in all_attrs:
            fname = attr.original_name
            if fname and fname not in res:
                res[fname] = {
                    'string': attr.name, 'type': type_map.get(attr.display_type, 'char'),
                    'store': False, 'manual': True, 'readonly': False,
                    'searchable': False, 'sortable': False, 'required': False,
                }
        return res

    # ==================== READ/WRITE FOR DYNAMIC FIELDS ====================
    def read(self, fields=None, load='_classic_read'):
        if not fields:
            return super().read(fields=fields, load=load)
        static = [f for f in fields if not str(f).startswith('x_')]
        dynamic = [f for f in fields if str(f).startswith('x_')]
        try:
            result = super().read(fields=static or None, load=load)
        except ValueError:
            result = super().read(fields=None, load=load)
        if dynamic:
            for data in result:
                brand = self.browse(data['id'])
                props = brand.dynamic_properties or {}
                if isinstance(props, str):
                    try:
                        props = json.loads(props)
                    except:
                        props = {}
                for f in dynamic:
                    data[f] = props.get(f, False)
        return result

    # ==================== ACTIONS ====================
    def create_product_brand(self):
        return {
            'type': 'ir.actions.act_window', 'res_model': 'product.brand',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_brand_split_view_custom').id,
            'target': 'current',
            'context': {
                'default_company_id': self.env.company.id,
                'default_is_create_mode': True,
                'default_master_brand_ids': self.env['product.brand'].search([
                    ('company_id', '=', self.env.company.id)
                ], order='create_date desc').ids,
            },
        }

    def save_brand(self):
        """Save and immediately reload the form with updated view"""
        self.ensure_one()
        self.write({'is_create_mode': False})
        if self.brand_attribute_ids:
            self._regenerate_brand_view()
        self.env['ir.ui.view'].clear_caches()
        self.env['ir.model.fields'].clear_caches()
        self.env.registry.clear_cache()
        self.invalidate_recordset()
        return {
            'type': 'ir.actions.client', 'tag': 'reload',
            'res_model': 'product.brand', 'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_brand_split_view_custom').id,
            'target': 'current',
            'context': {'active_id': self.id, 'res_id': self.id, 'brand_id': self.id},
        }

    def brand_open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'product.brand',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_brand_split_view_custom').id,
            'res_id': self.id,
            'context': {'active_id': self.id, 'res_id': self.id, 'brand_id': self.id},
        }

    def brand_master_unlink(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'brand.delete.confirmation.wizard',
            'view_mode': 'form', 'target': 'new',
            'context': {'default_brand_id': self.id}
        }

    def action_back_to_brand_menu(self):
        return {
            'type': 'ir.actions.act_window', 'name': 'Product Brands',
            'res_model': 'product.brand', 'view_mode': 'tree,form',
            'views': [
                (self.env.ref('pim_ext.view_product_brand_tree').id, 'list'),
                (self.env.ref('pim_ext.view_product_brand_split_view_custom').id, 'form'),
            ],
            'domain': [('company_id', '=', self.env.company.id)],
            'context': {'default_company_id': self.env.company.id},
            'target': 'current',
        }

    def action_open_add_attribute_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'brand.add.attribute.wizard',
            'view_mode': 'form', 'target': 'new',
            'context': {'default_brand_id': self.id}
        }


# ==================== BRAND ATTRIBUTES MODEL ====================
class BrandAttributes(models.Model):
    _name = 'brand.attributes'
    _description = 'Brand Attributes Configuration'

    brand_id = fields.Many2one('product.brand', 'Brand', ondelete='cascade', required=True)
    attribute_id = fields.Many2one('product.brand.attribute', string='Attribute',
                                   ondelete='cascade', required=True)
    attribute_company_id = fields.Many2one(related='attribute_id.company_id')
    attribute_group_id = fields.Many2one('product.brand.attribute.group',
                                         string='Attribute Group', required=True)
    is_visible = fields.Boolean(string='Visible', default=True,
                                help='Show this attribute in the Properties tab')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"{rec.attribute_id.name}"))
        return result

    def write(self, vals):
        """Log changes to parent brand's history"""
        old_values = {}
        for rec in self:
            old_values[rec.id] = {
                'is_visible': rec.is_visible,
                'attribute_group_id': rec.attribute_group_id.name if rec.attribute_group_id else False,
                'attribute_name': rec.attribute_id.name,
            }
        res = super(BrandAttributes, self).write(vals)
        for rec in self:
            changes = []
            old = old_values.get(rec.id, {})
            if 'is_visible' in vals and old.get('is_visible') != rec.is_visible:
                old_val = 'Yes' if old['is_visible'] else 'No'
                new_val = 'Yes' if rec.is_visible else 'No'
                changes.append(f"<li><strong>Visible ({old['attribute_name']})</strong>: {old_val} → {new_val}</li>")
            if 'attribute_group_id' in vals:
                old_group = old.get('attribute_group_id', 'N/A')
                new_group = rec.attribute_group_id.name if rec.attribute_group_id else 'N/A'
                if old_group != new_group:
                    changes.append(
                        f"<li><strong>Group ({old['attribute_name']})</strong>: {old_group} → {new_group}</li>")
            if changes:
                rec._log_to_brand_history(changes)
        if 'is_visible' in vals or 'attribute_group_id' in vals:
            for rec in self:
                rec.brand_id._regenerate_brand_view()
        return res

    def _log_to_brand_history(self, changes):
        """Add entry to brand's history log"""
        self.ensure_one()
        if not self.brand_id:
            return
        user = self.env.user.display_name
        updated = fields.Datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        msg = (f"<div style='border-left:3px solid #6C757D;padding-left:10px;'>"
               f"Updated by <strong>{user}</strong> on {updated}<ul>{''.join(changes)}</ul></div>")
        current_log = self.brand_id.history_log or ''
        self.brand_id.with_context(skip_history_log=True).write({'history_log': tools.html_sanitize(msg) + current_log})

    @api.model_create_multi
    def create(self, vals_list):
        records = super(BrandAttributes, self).create(vals_list)
        for rec in records:
            user = self.env.user.display_name
            created = fields.Datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            msg = (f"<div style='border-left:3px solid #28a745;padding-left:10px;'>"
                   f"Created by <strong>{user}</strong> on {created}<ul>"
                   f"<li><strong>Added Attribute</strong>: {rec.attribute_id.name}</li>"
                   f"<li><strong>Group</strong>: {rec.attribute_group_id.name}</li>"
                   f"<li><strong>Visible</strong>: {'Yes' if rec.is_visible else 'No'}</li></ul></div>")
            current_log = rec.brand_id.history_log or ''
            rec.brand_id.with_context(skip_history_log=True).write(
                {'history_log': tools.html_sanitize(msg) + current_log})
        brands = records.mapped('brand_id')
        for brand in brands:
            brand._regenerate_brand_view()
        return records

    def unlink(self):
        brands_data = []
        for rec in self:
            brands_data.append({
                'brand': rec.brand_id, 'attr_name': rec.attribute_id.name,
                'group_name': rec.attribute_group_id.name, 'was_visible': rec.is_visible,
            })
        res = super(BrandAttributes, self).unlink()
        for data in brands_data:
            if data['brand'].exists():
                user = self.env.user.display_name
                deleted = fields.Datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                msg = (f"<div style='border-left:3px solid #dc3545;padding-left:10px;'>"
                       f"Deleted by <strong>{user}</strong> on {deleted}<ul>"
                       f"<li><strong>Removed Attribute</strong>: {data['attr_name']}</li>"
                       f"<li><strong>Group</strong>: {data['group_name']}</li>"
                       f"<li><strong>Was Visible</strong>: {'Yes' if data['was_visible'] else 'No'}</li></ul></div>")
                current_log = data['brand'].history_log or ''
                data['brand'].with_context(skip_history_log=True).write(
                    {'history_log': tools.html_sanitize(msg) + current_log})
                data['brand']._regenerate_brand_view()
        self.env['product.brand']._cleanup_invalid_dynamic_views()
        return res


# ==================== BRAND ATTRIBUTE SEQUENCE ====================
class BrandAttributeSequence(models.Model):
    _name = 'brand.attribute.sequence'
    _description = 'Brand Attribute Sequence'

    attr_group_ids = fields.One2many('brand.attribute.seq.line', 'brand_sequence_id', string="Attribute Group")
    brand_id = fields.Many2one('product.brand', 'Brand', required=True)
    exist_group_ids = fields.Many2many('product.brand.attribute.group', related='brand_id.exist_group_ids')
    name = fields.Char(related='brand_id.name')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        brand_id = self.env['product.brand'].browse(ctx.get('default_brand_id'))
        if brand_id and brand_id.exist_group_ids:
            lines = []
            for idx, grp in enumerate(brand_id.exist_group_ids.sorted('sequence')):
                lines.append((0, 0, {'attribute_group_id': grp.id, 'sequence': (idx + 1) * 10}))
            res['attr_group_ids'] = lines
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super(BrandAttributeSequence, self).create(vals_list)
        for rec in records:
            if rec.brand_id:
                rec.brand_id.brand_sequence_id = rec.id
        return records

    def confirm_sequence(self):
        """Apply the sequence and clear caches"""
        self.env['ir.ui.view'].clear_caches()
        return {'type': 'ir.actions.act_window_close'}


class BrandAttributeSequenceLines(models.Model):
    _name = 'brand.attribute.seq.line'
    _description = 'Brand Attribute Sequence Line'
    _order = 'sequence, id'

    sequence = fields.Integer("Sequence", default=10)
    attribute_group_id = fields.Many2one('product.brand.attribute.group',
                                         string='Attribute Group', required=True)
    brand_sequence_id = fields.Many2one('brand.attribute.sequence', string='Brand Sequence',
                                        required=True, ondelete='cascade')
    attr_grp_company_id = fields.Many2one(related='attribute_group_id.company_id', store=True)


# ==================== DELETE WIZARD ====================
class BrandDeleteConfirmationWizard(models.TransientModel):
    _name = 'brand.delete.confirmation.wizard'
    _description = 'Brand Delete Confirmation'

    brand_id = fields.Many2one('product.brand', string='Brand', required=True)
    brand_name = fields.Char(related='brand_id.name', readonly=True)
    product_count = fields.Integer(related='brand_id.product_count', readonly=True)
    confirmation_message = fields.Html(compute='_compute_confirmation_info', readonly=True)
    product_names = fields.Html(compute='_compute_confirmation_info', readonly=True)

    @api.depends('brand_id')
    def _compute_confirmation_info(self):
        for rec in self:
            if not rec.brand_id:
                rec.confirmation_message = ""
                rec.product_names = ""
                continue
            products = self.env['product.template'].search([('brand_id', '=', rec.brand_id.id)], limit=10)
            if rec.product_count > 0:
                rec.confirmation_message = (
                    "<p>Deleting this brand will remove the brand association from these products. "
                    "Are you sure you want to proceed?</p>")
                prod_list = "<ul>" + "".join([f"<li>{p.name}</li>" for p in products]) + "</ul>"
                if rec.product_count > 10:
                    prod_list += f"<p><em>...and {rec.product_count - 10} more.</em></p>"
                rec.product_names = prod_list
            else:
                rec.confirmation_message = f"<p>Are you sure you want to delete the brand <strong>{rec.brand_id.name}</strong>?</p>"
                rec.product_names = ""

    def confirm_delete(self):
        """Delete brand and always navigate to a safe destination"""
        self.ensure_one()
        if not self.brand_id.exists():
            return {'type': 'ir.actions.act_window_close'}
        deleted_brand_id = self.brand_id.id
        company_id = self.brand_id.company_id.id or self.env.company.id
        affected = self.env['product.template'].search([('brand_id', '=', deleted_brand_id)])
        if affected:
            affected.with_context(skip_history_log=True).write({'brand_id': False})
        self.brand_id.with_context(allow_force_delete=True).unlink()
        next_brand = self.env['product.brand'].search([('company_id', '=', company_id)],
                                                      limit=1, order='create_date desc')
        if next_brand:
            return {
                'type': 'ir.actions.act_window', 'res_model': 'product.brand',
                'res_id': next_brand.id, 'view_mode': 'form',
                'view_id': self.env.ref('pim_ext.view_product_brand_split_view_custom').id,
                'target': 'current', 'flags': {'mode': 'readonly'},
            }
        else:
            return {
                'type': 'ir.actions.act_window', 'res_model': 'product.brand',
                'view_mode': 'list,form', 'target': 'current',
            }


# ==================== ATTRIBUTE WIZARDS ====================
class BrandAddAttributeWizard(models.TransientModel):
    _name = 'brand.add.attribute.wizard'
    _description = 'Add Single Attribute Wizard'

    brand_id = fields.Many2one('product.brand', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    existing_attribute_ids = fields.Many2many('product.brand.attribute',
                                              related='brand_id.exist_attribute_ids', readonly=True)
    attribute_group_id = fields.Many2one('product.brand.attribute.group', string='Attribute Group',
                                         domain="[('company_id', '=', company_id)]")
    attribute_id = fields.Many2one('product.brand.attribute', string='Attribute',
                                   domain="[('company_id', '=', company_id), ('id', 'not in', existing_attribute_ids)]")

    @api.onchange('attribute_group_id')
    def _onchange_attribute_group_id(self):
        domain = [('company_id', '=', self.company_id.id), ('id', 'not in', self.existing_attribute_ids.ids)]
        if self.attribute_group_id:
            domain.append(('group_id', '=', self.attribute_group_id.id))
        return {'domain': {'attribute_id': domain}}

    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        if self.attribute_id and self.attribute_id.group_id:
            self.attribute_group_id = self.attribute_id.group_id

    def confirm_add_attribute(self):
        self.ensure_one()
        if self.attribute_id:
            group_id = self.attribute_group_id.id or self.attribute_id.group_id.id
            if not group_id:
                raise UserError(_("The selected attribute does not belong to a group."))
            self.env['brand.attributes'].create({
                'brand_id': self.brand_id.id,
                'attribute_id': self.attribute_id.id,
                'attribute_group_id': group_id
            })
            return {
                'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {
                    'title': _('Attribute Added'),
                    'message': _('Click the SAVE button to see the new field in the form.'),
                    'type': 'success', 'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        return {'type': 'ir.actions.act_window_close'}


# ==================== PRODUCT TEMPLATE ====================
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Brand', tracking=True,
                               domain="[('company_id', '=', company_id)]", ondelete='set null')
    brand_logo = fields.Image(related='brand_id.brand_logo', readonly=True, store=False)
    brand_tagline = fields.Char(related='brand_id.tagline', readonly=True, store=False)
    brand_country = fields.Many2one(related='brand_id.country_of_origin', readonly=True, store=False)
    brand_website = fields.Char(related='brand_id.website', readonly=True, store=False)
    brand_description = fields.Text(related='brand_id.description', readonly=True, store=False)
    brand_seo_title = fields.Char(related='brand_id.seo_title', readonly=True, store=False)
    brand_seo_keywords = fields.Char(related='brand_id.seo_keywords', readonly=True, store=False)
    brand_seo_description = fields.Text(related='brand_id.seo_description', readonly=True, store=False)

    def write(self, vals):
        result = super(ProductTemplate, self).write(vals)
        if 'brand_id' in vals:
            self.env['ir.ui.view'].clear_caches()
        return result


# ==================== ATTRIBUTE GROUP ====================
class ProductBrandAttributeGroup(models.Model):
    _name = 'product.brand.attribute.group'
    _description = 'Brand Attribute Group'
    _order = 'sequence, id'

    name = fields.Char('Group Name', required=True, translate=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    is_system = fields.Boolean(string='System Group', default=False, help='Built-in form groups')
    technical_name = fields.Char(string='Technical Name', help='Internal identifier for system groups')


# ==================== ATTRIBUTE DEFINITION ====================
class ProductBrandAttribute(models.Model):
    _name = 'product.brand.attribute'
    _description = 'Brand Attribute Definition'
    _order = 'sequence, id'

    name = fields.Char('Attribute Name', required=True, translate=True)
    original_name = fields.Char('Field Code', compute='_compute_original_name', store=True,
                                readonly=False, help="Auto-generated technical name (must start with x_)", copy=False)
    sequence = fields.Integer(default=10)
    group_id = fields.Many2one('product.brand.attribute.group', string="Group")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    is_mandatory = fields.Boolean(string="Mandatory on Brand")
    display_type = fields.Selection([
        ('text', 'Text'), ('textarea', 'Text Area'), ('image', 'Image'),
        ('simple_select', 'Dropdown'), ('multi_select', 'Tags'), ('price', 'Monetary'),
        ('date', 'Date'), ('file', 'File'), ('color', 'Color'),
        ('boolean', 'Checkbox'), ('integer', 'Integer'), ('float', 'Float'),
    ], string="Type", default='text', required=True)
    value_ids = fields.One2many('product.brand.attribute.value', 'attribute_id', string="Values")

    _sql_constraints = [
        ('original_name_uniq', 'unique (original_name)', 'The Field Code must be unique!')
    ]

    @api.depends('name')
    def _compute_original_name(self):
        """Auto-generate original_name from name if not set or invalid"""
        for rec in self:
            if rec.original_name and rec.original_name.startswith('x_'):
                continue
            if rec.name:
                base_name = rec.name.lower()
                clean_name = re.sub(r'[^a-z0-9_]', '', base_name.replace(' ', '_'))
                clean_name = re.sub(r'_+', '_', clean_name)
                clean_name = clean_name.strip('_')
                proposed_name = f"x_{clean_name}" if clean_name else "x_attribute"
                counter = 1
                final_name = proposed_name
                while self.search([('original_name', '=', final_name), ('id', '!=', rec.id)], limit=1):
                    final_name = f"{proposed_name}_{counter}"
                    counter += 1
                rec.original_name = final_name
            else:
                rec.original_name = 'x_attribute'

    @api.constrains('original_name')
    def _check_original_name(self):
        """Ensure original_name always starts with x_"""
        for rec in self:
            if rec.original_name and not rec.original_name.startswith('x_'):
                raise ValidationError(_("Field Code must start with 'x_'. Got: %s\nIt will be auto-generated as: x_%s")
                                      % (rec.original_name, rec.original_name))
            if rec.original_name and not re.match(r'^x_[a-z0-9_]', rec.original_name):
                raise ValidationError(
                    _("Field Code can only contain lowercase letters, numbers, and underscores.\nGot: %s")
                    % rec.original_name)

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-fix original_name on create"""
        for vals in vals_list:
            if 'original_name' in vals:
                original = vals['original_name']
                if original and not original.startswith('x_'):
                    clean = re.sub(r'[^a-z0-9_]', '', original.lower())
                    vals['original_name'] = f"x_{clean}" if clean else False
        records = super(ProductBrandAttribute, self).create(vals_list)
        records._compute_original_name()
        return records

    def write(self, vals):
        """Auto-fix original_name on write"""
        if 'original_name' in vals:
            original = vals['original_name']
            if original and not original.startswith('x_'):
                clean = re.sub(r'[^a-z0-9_]', '', original.lower())
                vals['original_name'] = f"x_{clean}" if clean else False
        result = super(ProductBrandAttribute, self).write(vals)
        if 'original_name' in vals or 'name' in vals:
            brand_attrs = self.env['brand.attributes'].search([('attribute_id', 'in', self.ids)])
            brands = brand_attrs.mapped('brand_id')
            for brand in brands:
                brand._regenerate_brand_view()
        return result


class ProductBrandAttributeValue(models.Model):
    _name = 'product.brand.attribute.value'
    _description = 'Brand Attribute Selection Value'
    _order = 'sequence, id'

    name = fields.Char('Value', required=True, translate=True)
    sequence = fields.Integer(default=10)
    attribute_id = fields.Many2one('product.brand.attribute', string="Attribute", ondelete='cascade')
