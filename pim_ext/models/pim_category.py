# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import pytz


class PimCategory(models.Model):
    _name = 'pim.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Category'
    _order = 'complete_name'
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True, translate=False)
    categ_name = fields.Char(string='Name')
    category_id = fields.Many2one('product.category')
    code = fields.Char(string='Code')
    complete_name = fields.Char(
        'Complete Name', compute="_compute_complete_name", recursive=True, store=True)
    parent_id = fields.Many2one('pim.category', string='Parent Category')
    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")
    # category_active = fields.Boolean(related='category_id.active')
    active = fields.Boolean(default=True)
    child_ids = fields.One2many('pim.category', 'parent_id')
    is_last_level = fields.Boolean(string="Last Level", default=True)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    # Field for split view - holds all categories for the list view
    master_category_ids = fields.One2many('pim.category', compute='_compute_master_category_ids')

    @api.depends_context('company')
    def _compute_master_category_ids(self):
        """Compute all categories for display in the left list"""
        for record in self:
            categories = self.env['pim.category'].search([
                ('company_id', 'in', self.env.companies.ids)
            ])
            record.master_category_ids = categories

    def action_open_category_form(self):
        """ Opens the selected category in the custom split view """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pim.category',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_pim_category_split_custom').id,
            'res_id': self.id,
            'target': 'current',
        }
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.model_create_multi
    def create(self, vals):
        res = super(PimCategory, self).create(vals)
        for rec in res:
            if rec.parent_id:
                rec.parent_id.is_last_level = False
        self._log_changes(res, vals, action="create")
        return res

    def action_open_child_wizard(self):
        """ Opens the create form with the current
        category set as parent """
        self.ensure_one()
        return {
            'name': _('Create Sub-Category'),
            'type': 'ir.actions.act_window',
            'res_model': 'pim.category',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_pim_category_split_custom').id,
            'target': 'current',
            'context': {
                'default_parent_id': self.id,
                'form_view_initial_mode': 'edit',
            },
        }

    def _log_changes(self, rec, vals, action):
        # Get the current time in UTC
        updated_write_date_utc = fields.Datetime.now()
        # Convert to the user's timezone
        user_tz = self.env.user.tz or 'UTC'  # Default to UTC if no timezone is set
        updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")

        new_write_uid = self.env.user.display_name
        changes = []  # Store changes in list

        for key in vals:
            if key in ['name', 'code', 'active', 'parent_id']:
                attribute = rec._fields[key].string

                if key == 'parent_id':
                    old_value = rec.parent_id.display_name if rec.parent_id else 'N/A'
                    new_value = self.env['pim.category'].browse(vals[key]).display_name if vals.get(key) else 'N/A'
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

    def write(self, vals):
        for rec in self:
            self._log_changes(rec, vals, action="update")  # Call the common function with action as "update"
        return super(PimCategory, self).write(vals)


    def category_edit_open_form_view(self):
        """Open the category in edit mode in split view"""
        self.ensure_one()
        form_view_id = self.env.ref('pim_ext.view_pim_category_split_custom').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Category',
            'res_model': 'pim.category',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'views': [(form_view_id, 'form')],
            'context': {'form_view_initial_mode': 'edit'}
        }

    def category_master_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'category.master.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_category_id': self.id},
        }

    def create_pim_category(self):
        """Open the create category form"""
        form_view_id = self.env.ref('pim_ext.view_pim_category_split_custom_create').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Category',
            'res_model': 'pim.category',
            'view_mode': 'form',
            'view_id': form_view_id,
            'target': 'current',
            'views': [(form_view_id, 'form')],
            'context': {
                'default_master_category_ids': self.env['pim.category'].search([]).ids,
                'no_breadcrumbs': True,
                'form_view_initial_mode': 'edit',
            },
        }

    def action_back_to_category_menu(self):
        menu_id = self.env.ref('pim_ext.menu_pim_categories')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    def action_save_category(self):
        """Save category and show notification"""
        self.ensure_one()
        # Clear the editing session after save
        self.clear_edit_session()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Category saved successfully',
                'type': 'success',
                'sticky': False,
            }
        }


class ProductCategory(models.Model):
    _inherit = 'product.category'

    name = fields.Char(translate=True)
    code = fields.Char(string='Code')
    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")
    active = fields.Boolean(default=True)

    def action_home_page(self):
        """ Redirect to the home page of knowledge, which displays an article.
        Chosen articles comes from

          * either self if it is not void (taking the first article);
          * ``res_id`` key from context;
          * find the first accessible article, based on favorites and sequence
            (see ``_get_first_accessible_article``);
        """
        category = self[0] if self else False
        if not category and self.env.context.get('res_id', False):
            category = self.browse([self.env.context["res_id"]])
            if not category.exists():
                raise UserError(_("The Article you are trying to access has been deleted"))
        if not category:
            category = self.env['product.category'].search([("parent_id", "=", False)], limit=1)

        action = self.env['ir.actions.act_window']._for_xml_id('pim_ext.action_pim_categories')
        action['res_id'] = category.id
        return action

    def create_new_category(self, parent_id, name):
        new_id = self.env['product.category'].create({'name': name, 'parent_id': parent_id})
        return {'category_tree': self.return_categories_hierarchy(), 'new_id': new_id.id}

    def update_parent_category(self, child_id, new_parent_id):
        child_categ = self.env['product.category'].browse(child_id)
        parent_categ = self.env['product.category'].browse(new_parent_id)
        child_categ.parent_id = parent_categ
        return self.return_categories_hierarchy()


    def return_categories_recursive(self):
        """
        The method to go by all categories recursively to prepare their list in js_tree format

        Extra info:
         * Expected singleton
        """
        res = {"id": self.id, "text": self.name}
        child_res = []
        child_ids = self.search([("id", "in", self.child_id.ids)])
        for child in child_ids:
            child_res.append(child.return_categories_recursive())
        res.update({"children": child_res})
        return res

    def _log_changes(self, rec, vals, action):
        # Get the current time in UTC
        updated_write_date_utc = fields.Datetime.now()
        # Convert to the user's timezone
        user_tz = self.env.user.tz or 'UTC'  # Default to UTC if no timezone is set
        updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")

        new_write_uid = self.env.user.display_name
        changes = []  # Store changes in list

        for key in vals:
            if key in ['name', 'code', 'active', 'parent_id', 'complete_name']:
                attribute = rec._fields[key].string

                if key == 'parent_id':
                    old_value = rec.parent_id.display_name if rec.parent_id else 'N/A'
                    new_value = self.env['product.category'].browse(vals[key]).display_name if vals.get(key) else 'N/A'
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

    def write(self, vals):
        for rec in self:
            self._log_changes(rec, vals, action="update")  # Call the common function with action as "update"
        return super(ProductCategory, self).write(vals)

    @api.model_create_multi
    def create(self, vals):
        res = super(ProductCategory, self).create(vals)
        self._log_changes(res, vals, action="create")
        return res

    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.constrains('name')
    def check_name(self):
        if self.env['product.category'].search([('name', '=', self.name), ('id', '!=', self.id)]):
            raise ValidationError("The category name already exists.")

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.complete_name



    def save_attributes(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.category',
            'view_id': self.env.ref('pim_ext.view_form_pim_categories').id,
            'res_id': self.id,
            'context': {'no_breadcrumbs': True},
            'target': 'current',
        }

    # def category_edit_open_form_view(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Edit Category',
    #         'res_model': 'product.category',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('pim_ext.view_form_pim_categories').id,
    #         'context': {'no_breadcrumbs': True},
    #         'res_id': self.id,
    #     }

    def category_master_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'category.master.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_category_id': self.id},
        }

    def action_back_to_category_menu(self):
        menu_id = self.env.ref('pim_ext.menu_pim_categories')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }


class CategoryMasterUnlinkWizard(models.TransientModel):
    _name = 'category.master.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Category master'

    category_id = fields.Many2one('pim.category', string="Category Master")

    def confirm_unlink(self):
        """Confirm and delete the category"""
        if self.category_id:
            category_name = self.category_id.name
            self.category_id.unlink()

            # Return to category list and show success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Deleted',
                    'message': f'Category "{category_name}" has been deleted successfully',
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }



class ProductCategroyMapping(models.Model):
    _name = 'product.category.mapping'
    _description = "Map Product Category"

    is_primary = fields.Boolean('Primary', default=False)
    product_id = fields.Many2one('product.template', ondelete='cascade')
    not_available_categ_ids = fields.Many2many('pim.category', ondelete="cascade")
    family_category_id = fields.Many2one('pim.category', required=True, ondelete="cascade")
