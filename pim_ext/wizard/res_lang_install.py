from odoo import models, fields


class BaseLanguageInstall(models.TransientModel):
    _inherit = "base.language.install"

    def create_language_fields(self, vals, model):
        """ANAND MC OCT 10 2025 ()
        create new field names based on the new field(vals)"""
        if not vals:
            return False
        for rec in vals:
            self.env["ir.model.fields"].sudo().create({"name": rec.get("name"),
                                                       "model": model.model,
                                                       "model_id": model.id,
                                                       "field_description": rec.get("lang_name"),
                                                       "ttype": "char",
                                                       "state": "manual",
                                                       })

    def prepare_attribute_arch_view(self, all_fields):
        arch_lines = [
            '<xpath expr="//notebook" position="inside">',
            '    <page string="Label Translations" invisible="value_per_locale == \'no\'">',
            '        <group>',
            '           <group>',
        ]
        for field in all_fields:
            arch_lines.append(
                f'                <field name="{field['name']}" invisible="original_name != \'{field['or_name']}\'"/>')
        arch_lines += [
            '           </group>',
            '        </group>',
            '    </page>',
            '</xpath>',
        ]
        return "\n".join(arch_lines)

    def create_attribute_translation_view(self, all_fields, model):
        """ ANAND MC - OCT 10 2025
        Creates Label Translation View in product attribute form view"""
        base_view_id = self.env.ref("pim_ext.view_product_attribute_master_custom")
        inherited_view = self.env['ir.ui.view'].search([('name', '=', 'product_attribute_form_inherit_translation')])
        arch = self.prepare_attribute_arch_view(all_fields)
        if inherited_view:
            inherited_view.write({"arch": arch})
        else:
            self.env['ir.ui.view'].create({
                'name': 'product_attribute_form_inherit_translation',
                'type': 'form',
                'model': model.model,
                'model_id': model.id,
                'active': True,
                'inherit_id': base_view_id.id,
                'mode': 'extension',
                'arch': arch
            })
        return True

    def update_product_attribute_langs(self, attr=None):
        if not attr:
            attr = self.env['product.attribute'].search([])
        langs = self.env['res.lang'].search([('active', '=', True)])
        model = self.env['ir.model'].search([('model', '=', "product.attribute")], limit=1)
        all_fields, new_fields = attr.prepare_lang_translation_field_names(langs)
        self.create_language_fields(new_fields, model)
        attr.apply_translated_values(new_fields)
        self.create_attribute_translation_view(all_fields, model)

    def lang_install(self):
        action = super(BaseLanguageInstall, self).lang_install()
        # self.update_product_attribute_langs()
        return action
