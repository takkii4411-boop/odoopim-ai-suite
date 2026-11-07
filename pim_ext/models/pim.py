from odoo import api, fields, models, _


class ProductManagement(models.Model):
    _name = "product.management"
    _rec_name = "sku"
    _description = "manage and maintain product data"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    #General info
    sku = fields.Char(string="SKU")
    name = fields.Char(string="Name")
    moq = fields.Char(string="MOQ")
    description = fields.Text(string="Description")
    barcode = fields.Integer(string="Barcode")
    active = fields.Boolean(string="Active")

    family_id = fields.Many2one("family.attribute", string="Family")
    pim_category_id = fields.Many2one("pim.category", string="Category")
    chennel_id = fields.Many2one("pim.channel", string="Channel")

    #Pricing & Inventory
    lst_price = fields.Float(string="Sale Price")
    special_price = fields.Float(string="Special Price")
    special_price_start_date = fields.Date(string="Special Price Start Date")
    special_price_end_date = fields.Date(string="Special Price End Date")

    #Development History
    revision = fields.Char(string="Revision")
    revision_date = fields.Date(string="Revision Date")


    def pim_product_creation(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Attribute',
            'res_model': 'product.family.select',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_family_select_customs').id,
            'target': 'current',
            'context': {
                # 'default_attribute_ids': self.env['product.attribute'].search([]).ids,
            },
        }


