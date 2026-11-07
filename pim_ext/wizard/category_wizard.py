from datetime import datetime
from markupsafe import Markup
from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class CategoryWizard(models.TransientModel):
    _name = 'category.wizard'
    _description = "Category Wizard"

    family_ids = fields.Many2many('family.attribute')
    product_ids = fields.Many2many('product.template')
    category_ids = fields.One2many('category.wizard.line', 'wizard_id')
    mode = fields.Selection([('add_comp','add_comp'), ('add_taxonomy','add_taxonomy')])
    selected_category_id = fields.Many2one('pim.category', 'Category')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        print("default get function -----------------------------------------------------",fields_list)
        categories = self.env['pim.category'].search([])
        print("categories === ", categories)
        lines = []
        for cat in categories:
            lines.append((0, 0, {
                'pim_category_id': cat.id,
                'select': False,  # optional, since default is False
            }))
        print("lines === ", lines)
        res['category_ids'] = lines
        return res


    def add_taxonomy(self):
        if not self.category_ids.filtered(lambda x:x.select):
            raise ValidationError("Please choose Category.")
        family_categ = {}
        for categ in self.category_ids:
            if categ.select:
                for family in self.family_ids:
                    related_category_ids = family.taxonomy_ids.mapped('family_category_id')
                    if categ.category_id not in related_category_ids:
                        val = {'family_id':family.id,'is_primary': False, 'family_category_id': categ.category_id.id}
                        taxonomy = self.env['family.category.mapping'].create(val)
                        if family_categ.get(family.id):
                            family_categ[family.id].append(categ.category_id.complete_name)
                        else:
                            family_categ[family.id] = [categ.category_id.complete_name]

                    if not family.primary_taxonomy_id and family.taxonomy_ids:
                        family.primary_taxonomy_id = family.taxonomy_ids[0]
                        family.primary_taxonomy_id.is_primary = True
                        family.primary_category_id = family.taxonomy_ids[0].family_category_id
                    family.related_category_ids = family.taxonomy_ids.mapped('family_category_id')

        if  family_categ:
            details_header = (
                "<table><tr><th style='border:1px solid #d8dadd;text-align:left;text-wrap: nowrap;'>"
                "Categories</th></tr>")
            for family in self.family_ids:
                categories = '<ul><li>'+('</li><li>').join(family_categ[family.id])+'</li></ul>'
                msg = "<br/>Taxonomies added at "+datetime.now().strftime("%d/%m/%Y %H:%M:%S") + details_header + (
                    ("<tr><td style='border:1px solid #d8dadd;text-align:left;'>{categ} </td></tr>").format(categ=str(categories))) + "</table"
                msg = (Markup(msg))
                family.message_post(body=msg, body_is_html=True)

        return {
            'name': 'Successful',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.pop.message',
            'target': 'new',
            'context': {'default_name': "Successfully Added Taxonomies."}
        }

    def add_complementary(self):
        family_categ = {}
        if not self.category_ids.filtered(lambda x:x.select):
            raise ValidationError("Please choose Category.")
        for categ in self.category_ids:
            if categ.select:
                for family in self.family_ids:
                    complementary_categ_ids = family.complementary_categ_ids.mapped('family_category_id')
                    if categ.category_id not in complementary_categ_ids:
                        val = {'family_id':family.id,'is_primary': False, 'family_category_id': categ.category_id.id}
                        self.env['family.category.mapping_2'].create(val)
                        if family_categ.get(family.id):
                            family_categ[family.id].append(categ.category_id.complete_name)
                        else:
                            family_categ[family.id] = [categ.category_id.complete_name]

        if  family_categ:
            details_header = (
                "<table><tr><th style='border:1px solid #d8dadd;text-align:left;text-wrap: nowrap;'>"
                "Categories</th></tr>")
            for family in self.family_ids:
                categories = '<ul><li>'+('</li><li>').join(family_categ[family.id])+'</li></ul>'
                msg = "<br/>Complementary categories added at " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + details_header + (
                    ("<tr><td style='border:1px solid #d8dadd;text-align:left;'>{categ} </td></tr>").format(
                        categ=str(categories))) + "</table"
                msg = (Markup(msg))
                family.message_post(body=msg, body_is_html=True)
        return {
            'name': 'Successful',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.pop.message',
            'target': 'new',
            'context': {'default_name': "Successfully Added complementary categories."}
        }

    def action_update(self):
        print("category action_update ===============")
        for rec in self:
            selected_categories = rec.category_ids.filtered(lambda l: l.select).mapped('pim_category_id')
            print("selected_categories === ", selected_categories)
            if selected_categories:
                for p in rec.product_ids:
                    p.pim_category_ids = [(4, cat.id) for cat in selected_categories]

    def update_category(self, category_id, product_ids):
        wizard = self.browse(self.env.context.get("active_id"))
        print("wizard == ", wizard)
        print("update_category ===============",self, category_id)
        for rec in self:
            print("self product joiu", self.product_ids)
            selected_cats = category_id
            if selected_cats and product_ids:
                rec.selected_category_id = category_id
                products = self.env['product.template'].search([('id', 'in', product_ids)])
                print("products ============= ", products)
                for p in products:
                    print("p == ", p)
                    p.category_id = category_id
        return True


class CategoryWizardLine(models.TransientModel):
    _name = 'category.wizard.line'
    _description = "Category Wizard Line"

    select = fields.Boolean(default=False)
    pim_category_id = fields.Many2one('pim.category')
    category_id = fields.Many2one('product.category', related='pim_category_id.category_id')
    wizard_id = fields.Many2one('category.wizard')
