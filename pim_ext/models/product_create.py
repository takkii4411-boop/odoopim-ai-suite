# -*- coding: utf-8 -*-
import xml.etree.ElementTree as xee
from lxml import etree as xee
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
from lxml import etree
import re

class ProductCreate(models.Model):
    _name = 'product.create'
    _description ="Product Create"
    _rec_name = 'name'

    name = fields.Char(string='Name')

    master_products_ids = fields.One2many(
        'product.template',
        'parent_id',
        string='Products'
    )

    is_invisible = fields.Boolean(default=False, string='Invisible Types')
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)

    def action_back_to_product_menu(self):
        menu_id = self.env.ref('pim_ext.product_creation_menu')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    def create_product_rec(self):
        all_product_ids = self.env['product.template'].search([('company_id', '=', self.env.company.id)], order='create_date desc').ids
        return {
            'name': 'Product create',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_product_model_invisible': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_product_model(self):
        all_product_ids = self.env['product.template'].search([('company_id', '=', self.env.company.id)], order='create_date desc').ids
        return {
            'name': 'Create a Product model',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_invisible': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_bundle_product(self):
        all_product_ids = self.env['product.template'].search([('company_id', '=', self.env.company.id)], order='create_date desc').ids
        return {
            'name': 'Create a Bundle product',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_product_bundle': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_grouped_product(self):
        all_product_ids = self.env['product.template'].search([('company_id', '=', self.env.company.id)], order='create_date desc').ids
        return {
            'name': 'Create a Grouped product',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_product_grouped': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_product_rec_model(self):
        pass


class ProductCreateMaster(models.Model):
    _name = 'product.create.master'
    _description = 'Product creation page'
    _rec_name = 'sku'

    family_id = fields.Many2one('family.attribute', string='Family',required=False, ondelete='cascade',)
    sku = fields.Char(string='SKU')
    name = fields.Char(string='Name')
    image = fields.Binary("Product Image", attachment=True)
    image_ids = fields.One2many(
        'product.image',
        'product_create_id',
        string='Images'
    )
    master_products_ids = fields.One2many(
        'product.template',
        'product_master_id',
        string='Products'
    )

    is_invisible = fields.Boolean(default=False, string='Invisible Types')
    is_product_model_invisible = fields.Boolean(default=False, string='Invisible Types')
    is_product_grouped = fields.Boolean(default=False, string='Is Bundle')
    is_product_bundle = fields.Boolean(default=False, string='Is Grouped')
    variant_id = fields.Many2one('family.variant.line', string='Variants',
                                 domain="[('variant_family_id', '=', family_id)]")
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.company)
    image_url = fields.Char("Image URL")

    def action_back_to_product_menu(self):
        view_id = self.env.ref('pim_ext.view_product_template_custom_form')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

        return {
            'name': _('Leads'),
            'view_mode': 'list,form',
            'domain': [('lost_reason_id', 'in', self.ids)],
            'res_model': 'product.create',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'active_test': False},
        }

    def product_save(self):
        for rec in self:
            attributes = rec.family_id.mapped('family_attribute_ids').mapped('attribute_id')
            attributes_list = []
            for attribute in attributes:
                attributes_list.append(attribute.original_name)

            # Create the product record
            product_vals = {
                'name': rec.name if rec.name else 'Product',
                'default_code': rec.sku if rec.sku else 'SKU',
                'categ_id': 1,
                'sku': rec.sku,
                'is_variant': True if rec.variant_id else False,
                'variant_id': rec.variant_id.id,
                'is_update_from_attribute': True,
                # 'image_1920': self.image,
                'family_id': rec.family_id.id,
                'image_ids': rec.image_ids,
                'image_url': rec.image_url,
            }

            new_product = self.env['product.template'].create(product_vals)

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'form',
                'res_id': new_product.id,
                'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
                'context': {'no_breadcrumbs': True, 'default_family_id': rec.family_id.id},
                'target': 'current',
            }

    # def product_save(self):
    #     print("product_save =================")
    #     for rec in self:
    #         family_name = rec.family_id.name
    #         attributes_list = []
    #         new_field_xml = ''
    #
    #         # Get the attributes related to the current product's family (family_id)
    #         attributes = rec.family_id.mapped('family_attribute_ids').mapped('attribute_id')
    #         print("attributes =============", attributes)
    #         # Group attributes by their attribute_group (optional but can be helpful for UI)
    #         attribute_groups = {}  # This will store attributes grouped by their attribute_group.
    #         for attribute in attributes:
    #             for g in attribute.attribute_group:
    #                 attribute_group = g.name if attribute.attribute_group else 'Uncategorized'
    #                 if attribute_group not in attribute_groups:
    #                     attribute_groups[attribute_group] = []
    #                 attribute_groups[attribute_group].append(attribute)
    #             associated_family_id = rec.family_id.id  # Use the current product's family_id
    #         print("attribute_groups ============= ", attribute_groups)
    #         # Generate XML for each attribute group
    #         for group_name, group_attributes in attribute_groups.items():
    #             # Check if group should be invisible for the current family
    #             group_visible_condition = f'invisible="1 if family_id != {rec.family_id.id} else 0"'
    #
    #             new_field_xml += f'<group name="{group_name}" string="{group_name}" collapsible="1" expanded="1" >'
    #
    #             for attribute in group_attributes:
    #                 field_mandatory = attribute.is_mandatory
    #                 field_name = f"x_{attribute.name.replace(' ', '_').lower()}"
    #                 display_type = attribute.display_type
    #
    #                 created_field = self._create_dynamic_field(field_name, field_mandatory, display_type, attribute)
    #
    #                 # Add field to product template dynamically
    #                 attributes_list.append(field_name)
    #                 if attribute.display_type == 'radio':
    #                     field_name_xml = f'<field name="{field_name}" string="{attribute.name}" widget="radio"/>'
    #                 elif created_field.ttype == 'many2many':
    #                     field_name_xml = f'<field name="{field_name}" string="{attribute.name}" widget="many2many_tags"/>'
    #                 else:
    #                     field_name_xml = f'<field name="{field_name}" string="{attribute.name}"/>'
    #                 new_field_xml += field_name_xml
    #
    #             new_field_xml += '</group>'
    #
    #         variant_notebook_xml = ''
    #         if rec.variant_id:
    #             variant_lines = rec.variant_id.filtered(lambda v: v.variant_familiy_id == rec.family_id)
    #
    #             for variant in variant_lines:
    #                 for variant_rec in variant.variant_ids:
    #                     variant_name = variant_rec.name
    #                     field_name = f"x_{variant_name.replace(' ', '_').lower()}"
    #                     #
    #                     # self._create_dynamic_field(field_name, False, 'many2many')
    #
    #                     # Create a notebook page for each variant
    #                     # variant_visible_condition = f'invisible="1 if is_variant != True else 0"'
    #                     variant_visible_condition = f'invisible="1 if is_variant != True or family_id != {rec.family_id.id} else 0"'
    #                     # variant_notebook_xml += f"""
    #                     #         <page string="{variant_name}" name="{field_name}_page">
    #                     #             <field name="attribute_line_ids">
    #                     #
    #                     #             </field>
    #                     #         </page>
    #                     # """
    #
    #                     variant_invisible_rec = f'invisible="1 if is_variant_update != True else 0"'
    #                     variant_notebook_xml += f"""
    #                                     <page string="{variant_name}" name="{field_name}_page" {variant_visible_condition}>
    #                                         <form>
    #                                             <field name="is_variant_update" invisible="1"/>
    #                                             <header>
    #                                                 <button name = "update_variant_values" string = "Add values" icon="fa-plus " type = "object" class ="btn btn-success"/>
    #                                             </header>
    #                                             <sheet>
    #                                                 <group>
    #                                                     <group>
    #                                                         <field name="product_attr_values_id" string="Variant Values"  {variant_invisible_rec} widget="many2many_tags"/>
    #                                                     </group>
    #                                                 </group>
    #                                             </sheet>
    #                                         </form>
    #
    #                                     </page>
    #                             """
    #         group_visible_condition = f'invisible="1 if family_id != {rec.family_id.id} else 0"'
    #         if variant_notebook_xml:
    #             dynamic_notebook_xml = f"""
    #                     <xpath expr="//notebook/page[1]" position="before">
    #                         <page string="Attributes" name="attributes_page" {group_visible_condition}>
    #                             {new_field_xml}
    #                             <group name="product_image" string="Product Image" collapsible="1" expanded="1" >
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_1" style="font-weight: bold; text-align: center;">Image 1</label>
    #                                     <field name="image_1" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_2" style="font-weight: bold; text-align: center;">Image 2</label>
    #                                     <field name="image_2" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_3" style="font-weight: bold; text-align: center;">Image 3</label>
    #                                     <field name="image_3" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_4" style="font-weight: bold; text-align: center;">Image 4</label>
    #                                     <field name="image_4" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_5" style="font-weight: bold; text-align: center;">Image 5</label>
    #                                     <field name="image_5" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_6" style="font-weight: bold; text-align: center;">Image 6</label>
    #                                     <field name="image_6" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_7" style="font-weight: bold; text-align: center;">Image 7</label>
    #                                     <field name="image_7" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #
    #                                 <div style="display: flex; flex-direction: column; gap: 5px; margin-bottom: 15px;">
    #                                     <label for="image_8" style="font-weight: bold; text-align: center;">Image 8</label>
    #                                     <field name="image_8" widget="image"
    #                                            style="width: 80px; height: 80px; border: 1px solid #ccc; padding: 5px; border-radius: 8px;"/>
    #                                 </div>
    #                             </group>
    #                         </page>
    #                         {variant_notebook_xml}
    #                     </xpath>
    #                 """
    #         else:
    #             dynamic_notebook_xml = f"""
    #                         <xpath expr="//notebook/page[1]" position="before">
    #                             <page string="Attributes" name="attributes_page" {group_visible_condition}>
    #                                 {new_field_xml}
    #                             </page>
    #                         </xpath>
    #                     """
    #
    #         # Apply to the Default Product View
    #         default_view_id = self.env.ref('product.product_template_only_form_view').id
    #         self._update_or_create_view('sku_field_add_attribute_' + family_name.lower().replace(' ', '_'),
    #                                     'product.template', default_view_id, dynamic_notebook_xml)
    #
    #         # Apply to the Custom Split View
    #         custom_view_id = self.env.ref('pim_ext.view_product_creation_split_view_custom').id
    #         self._update_or_create_view('sku_field_add_attribute_custom_' + family_name.lower().replace(' ', '_'),
    #                                     'product.template', custom_view_id, dynamic_notebook_xml)
    #
    #         # Check if the x_product_name field exists
    #         x_product_name_field = f"x_{'product_name'.replace(' ', '_').lower()}"
    #         x_product_name_value = rec.name if rec.name and x_product_name_field in attributes_list else "Product"
    #
    #         # Create the product record
    #         product_vals = {
    #             'name': rec.name if rec.name else 'Product',
    #             'default_code': rec.sku if rec.sku else 'SKU',
    #             'categ_id': 1,
    #             'sku': rec.sku,
    #             'is_variant': True if rec.variant_id else False,
    #             'variant_id': rec.variant_id.id,
    #             'is_update_from_attribute': True,
    #             # 'image_1920': self.image,
    #             'family_id': rec.family_id.id,
    #         }
    #
    #         # Add the x_product_name field value if it exists
    #         if x_product_name_value:
    #             product_vals[x_product_name_field] = x_product_name_value
    #
    #         new_product = self.env['product.template'].create(product_vals)
    #
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'product.template',
    #             'view_mode': 'form',
    #             'res_id': new_product.id,
    #             'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
    #             'context': {'no_breadcrumbs': True, 'default_family_id': rec.family_id.id},
    #             'target': 'current',
    #         }
    #     return True


    def _create_dynamic_field(self, field_name, field_mandatory, display_type, attribute):
        """ Creates a dynamic field in product.template if it doesn't already exist """
        # Check if the field exists in product.template
        existing_field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])

        # Map display types to Odoo field types
        display_type_mapping = {
            'number': 'integer',
            'radio': 'selection',
            'file': 'binary',
            'image': 'binary',
            'link': 'char',
            'identifier': 'integer',
            'measurement': 'float',
            'multi_select': 'many2many',
            'price': 'float',
            'ref_data_multi': 'many2many',
            'ref_data_simple_select': 'many2many',
            'simple_select': 'selection',
            'text': 'char',
            'textarea': 'text',
            'yes_no': 'boolean',
            'pills': 'many2many',
            'select': 'selection',
            'color': 'selection',
            'multi': 'many2many',
        }

        # Get the correct display type
        ttype = display_type_mapping.get(display_type, 'char')  # Default to 'char' if not found

        if not existing_field:
            # Create the field with a user-friendly description
            create_field = self.env['ir.model.fields'].create({
                'name': field_name,
                'model_id': self.env['ir.model']._get('product.template').id,
                'field_description': self._format_field_description(attribute.name),  # Format the attribute name
                'ttype': ttype,  # Dynamic field type
                'store': True,
                'required': field_mandatory,
            })

            # Handle selection fields if applicable
            if ttype == 'selection' and attribute.value_ids:
                for value in attribute.value_ids:
                    sel_name = value.name
                    sel_value = value.name
                    self.env['ir.model.fields.selection'].create({
                        'name': sel_name,
                        'value': sel_value,
                        'field_id': create_field.id
                    })
            if ttype == 'many2many':
                # Create the relation model if it doesn't exist
                self.env['many2many.selection.values'].create({'name': value.name, 'field_name': field_name})
                # Update the field to set the relation
                create_field.write({
                    'relation': 'many2many.selection.values',
                    'domain': f"[('field_name', '=', '{field_name}')]",
                })

            print(f"Field '{field_name}' created dynamically in product.template with description '{attribute.name}'.")
        else:
            print(f"Field '{field_name}' already exists in product.template.")
            return existing_field

        return create_field

    def _format_field_description(self, field_name):
        """ Format the field name to a user-friendly description """
        # Capitalize the first letter of each word and replace underscores with spaces
        return ' '.join(word.capitalize() for word in field_name.split('_'))

    def _update_or_create_view(self, view_name, model_name, inherit_view_id, arch_value):
        model_id = self.env['ir.model'].search([('model', '=', model_name)])

        view_exist = self.env['ir.ui.view'].search([
            ('name', '=ilike', view_name),
            ('model_id', '=', model_id.id),
            ('active', 'in', [True, False])
        ])

        if view_exist:
            view_exist.arch = arch_value
        else:
            self.env['ir.ui.view'].sudo().create({
                'name': view_name,
                'type': 'form',
                'model': model_name,
                'inherit_id': inherit_view_id,
                'active': True,
                'arch': arch_value,
            })

    def product_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_mode': 'kanban',
            'view_id': self.env.ref('pim_ext.view_product_management_kanban').id,
            'context': {'no_breadcrumbs': True},
        }

class Many2manySelectionValues(models.Model):
    _name = 'many2many.selection.values'
    _description = "Many2many Selection Values"

    name = fields.Char()
    field_name = fields.Char()
