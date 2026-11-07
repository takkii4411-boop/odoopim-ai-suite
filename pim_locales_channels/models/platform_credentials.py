from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PlatformCredentials(models.Model):
    _inherit = "platform.credentials"

    platform_model_id = fields.Many2one("ir.model")

    def get_model_name(self):
        """create a model name for platform models"""
        name = f"{self.platform} locale save"
        model_name = 'x_' + name.replace(' ', '_')
        return name, model_name

    def prepare_field_vals(self):
        return [
            (0, 0, {'name': 'x_res_model', 'field_description': 'Declaration Model Name', 'ttype': 'char', 'required': True}),
            (0, 0, {'name': 'x_res_id', 'field_description': 'Record ID', 'ttype': 'many2one_reference'}),
            (0, 0, {'name': 'x_field_name', 'field_description': 'Field Name', 'ttype': 'char'}),
            (0, 0, {'name': 'x_ttype', 'field_description': 'Field Type', 'ttype': 'selection'}),
            (0, 0, {'name': 'x_lang_id', 'field_description': 'Language', 'ttype': 'many2one', 'relation': 'res.lang'}),
            (0, 0, {'name': 'x_value', 'field_description': 'Value', 'ttype': 'char', 'required': True}),
        ]

    def create_platform_model(self):
        """Create a model to save the channel translation values
        Creates corresponding model in ir.model to save values accordingly
        use : to resolve the fetch issue while search in large set of data,
        create multiple table to reduce the table record count"""
        model = self.env["ir.model"].sudo()
        for rec in self:
            if rec.is_active:
                name, model_name = rec.get_model_name()
                model_obj = model.search([('model', '=', model_name)])
                if not model_obj:
                    model_obj = model.create([{
                        'name': name,
                        'model': model_name,
                        'field_id': rec.prepare_field_vals()
                    }])
                    _logger.info(f"Created a new model {model_name}")
                rec.platform_model_id = model_obj.id
                _logger.info(f"Assigned {model_name} to platform credentials which already exist")

    @api.model_create_multi
    def create(self, vals_list):
        results = super(PlatformCredentials, self).create(vals_list)
        results.create_platform_model()
        return results
