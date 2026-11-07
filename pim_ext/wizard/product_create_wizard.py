from odoo import models, fields


class ProductCreateWizard(models.TransientModel):
    _name = "product.create.wizard"
    _description = "Create Product Wizard"

    model = fields.Char()
    product_create_type = fields.Selection([('none', 'PRODUCT'),
                                            ('product', 'CREATE PRODUCT'),
                                            ('model', 'CREATE PRODUCT MODEL'),
                                            ('bundle', 'CREATE PRODUCT BUNDLE'),
                                            ('group', 'CREATE PRODUCT GROUP'),
                                            ('progress', 'UNDER CONSTRUCTION')], default="none")
    name = fields.Char("Product Name")

    def _default_family_domain(self):
        return [('company_id','in', [self.env.company.id])]

    family_id = fields.Many2one("family.attribute", domain=_default_family_domain)
    family_variant_id = fields.Many2one("family.variant.line", "Varints",
                                        domain="[('variant_family_id', '=', family_id)]")
    is_sku_manual = fields.Boolean()
    sku = fields.Char()

    def action_back_menu(self):
        """ANAND MC 14 OCT 2015 - back to action and product menu"""
        if self.product_create_type != 'none':
            self.write({
                'product_create_type': 'none',
                'is_sku_manual': False,
                'name': '',
                'sku': '',
                'family_id': False,
                'family_variant_id': False
            })
        else:
            menu_id = self.env.ref('pim_ext.product_creation_menu')
            if self.model == 'product.product':
                menu_id = self.env.ref('pim_ext.product_product_creation_menu')
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'menu_id': menu_id.id,
                },
            }

    def create_main_product(self):
        """ANAND MC 14 OCT 2015 - Navigate to Main product creation Menu"""
        self.product_create_type = "product"

    def create_product_model(self):
        """ANAND MC 14 OCT 2015 - Navigate to product model creation Menu"""
        self.product_create_type = "model"

    def prepare_attribute_vals(self):
        """ANAND MC 14 OCT 2015 - Prepare attribute Vals for product Template"""
        variants = [(0, 0, {'attribute_id': x.id, 'value_ids': [y.id for y in x.value_ids]}) for x in
                    self.family_variant_id.variant_ids]
        return variants
    
    def add_attribute_to_family(self):
        adder = self.env['add.attribute.wizard'].create({'attribute_family_id': self.family_id.id,'attribute_ids':self.family_variant_id.variant_ids.ids})
        adder.add_attributes_to_family()
        self.family_id.update_view_in_sequence()

    def prepare_product_vals(self):
        """ANAND MC 14 OCT 2015 - prepare product template vals"""
        vals = {
            'name': self.name if self.name else 'Product',
            'default_code': self.sku if self.sku else 'SKU',
            'categ_id': 1,
            'sku': self.sku,
            'is_update_from_attribute': True,
            'family_id': self.family_id.id,
        }
        if self.product_create_type == 'model':
            vals['has_variant'] = True
            if self.family_variant_id:
                vals['variant_id'] = self.family_variant_id.id
                self.add_attribute_to_family()
                vals['attribute_line_ids'] = self.prepare_attribute_vals()
        return vals

    def action_save(self):
        """ANAND MC 14 OCT 2015 - on save create product"""
        product_template = self.env['product.template'].sudo()
        vals = self.prepare_product_vals()
        product = product_template.create(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': product.id,
            'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
            'context': {'no_breadcrumbs': True, 'default_family_id': self.family_id.id},
            'target': 'current',
        }

    def action_cancel(self):
        """ANAND MC 14 OCT 2015 - cancel action to navigate menus"""
        self.action_back_menu()

    def action_maintenance(self):
        """ANAND MC 14 OCT 2015 - Show Under construction features"""
        self.product_create_type = 'progress'
