# -*- coding: utf-8 -*-
from odoo import api, models
from ast import literal_eval


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """Override to add the current setting for char field capitalization to the session info."""
        result = super().session_info()
        icp_sudo = self.env['ir.config_parameter'].sudo()

        # Get enable/disable setting
        result['enable_char_capitalize'] = icp_sudo.get_param(
            'web_char_capitalize.enable_char_capitalize',
            default='False'
        ) == 'True'

        # Get excluded models
        excluded_models_param = icp_sudo.get_param(
            'web_char_capitalize.excluded_models_capitalize',
            default='[]'
        )

        try:
            excluded_model_ids = literal_eval(
                excluded_models_param) if excluded_models_param else []
        except (ValueError, SyntaxError):
            excluded_model_ids = []

        # Get the actual model names from ir.model
        if excluded_model_ids:
            excluded_models = self.env['ir.model'].sudo().browse(
                excluded_model_ids)
            result['excluded_models_capitalize'] = excluded_models.mapped(
                'model')
        else:
            result['excluded_models_capitalize'] = []

        # Get excluded fields
        excluded_fields_param = icp_sudo.get_param(
            'web_char_capitalize.excluded_fields_capitalize',
            default='[]'
        )

        try:
            excluded_field_ids = literal_eval(
                excluded_fields_param) if excluded_fields_param else []
        except (ValueError, SyntaxError):
            excluded_field_ids = []

        # Get the actual field names (model.field_name format) from ir.model.fields
        if excluded_field_ids:
            excluded_fields = self.env['ir.model.fields'].sudo().browse(
                excluded_field_ids)
            result['excluded_fields_capitalize'] = [
                f"{field.model}.{field.name}" for field in excluded_fields
            ]
        else:
            result['excluded_fields_capitalize'] = []

        return result
