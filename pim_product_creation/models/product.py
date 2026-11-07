from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_form_view_id(self):
        return self.env.ref("pim_ext.view_product_product_creation_split_view_custom").id

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_form_view_id(self):
        return self.env.ref("pim_ext.view_product_creation_split_view_custom").id
