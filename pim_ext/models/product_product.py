from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_back_to_product_menu(self):
        return {
            'name': 'Product Variant',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'views': [
                (self.env.ref('pim_ext.view_product_product_management_tree').id, 'list'),
                (self.env.ref('pim_ext.view_product_product_management_kanban').id, 'kanban'),
                (self.env.ref('pim_ext.view_product_product_creation_split_view_custom').id, 'form'),
            ],
            'domain': [('company_id', 'in', [self.env.company.id])],
            'view_mode': 'list,kanban,form',
            'target': 'current',
            'context': {
                'no_breadcrumbs': True,
            }
        }

    def save_product_rec(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.product',
            'view_id': self.env.ref('pim_ext.view_product_product_creation_split_view_custom').id,
            'res_id': self.id,
            'context': {'no_breadcrumbs': True},
            'target': 'current',
        }

    def create_pim_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CREATE PRODUCT',
            'res_model': 'product.create.wizard',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        "default_product_create_type": "none",
                        "default_model": "product.product",
                        },
            'target': 'current',
        }

    def custom_product_open_form_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Variant',
            'res_model': 'product.product',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_product_product_creation_split_view_custom').id,
            'context': {'no_breadcrumbs': True,
                        },
            'res_id': self.id,
        }

    def custom_product_open_default_form_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.product',
            'view_mode': 'form',
            'view_id': self.env.ref('product.product_normal_form_view').id,
            'context': {'no_breadcrumbs': True,
                        },
            'res_id': self.id,
            'target': 'new',
        }

    def custom_product_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'product_variant_id': self.id, 'no_breadcrumbs': True, },
        }
