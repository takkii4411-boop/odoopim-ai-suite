# -*- coding: utf-8 -*-
from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    """Inherits ResConfigSettings to add char field capitalize configuration."""
    _inherit = 'res.config.settings'

    enable_char_capitalize = fields.Boolean(
        string="Enable Char Field Auto Capitalize",
        config_parameter="web_char_capitalize.enable_char_capitalize",
        help="When enabled, automatically capitalizes the first letter of all char field inputs."
    )

    excluded_models_capitalize = fields.Many2many(
        'ir.model',
        'res_config_capitalize_model_rel',
        'config_id',
        'model_id',
        string="Excluded Models",
        help="Select models where char field capitalization should NOT be applied."
    )

    excluded_fields_capitalize = fields.Many2many(
        'ir.model.fields',
        'res_config_capitalize_field_rel',
        'config_id',
        'field_id',
        string="Excluded Fields",
        help="Select specific char fields where capitalization should NOT be applied."
    )

    def set_values(self):
        """Save the many2many field values to ir.config_parameter."""
        res = super(ResConfigSettings, self).set_values()
        icp_sudo = self.env['ir.config_parameter'].sudo()

        # Save excluded models
        icp_sudo.set_param(
            'web_char_capitalize.excluded_models_capitalize',
            self.excluded_models_capitalize.ids
        )

        # Save excluded fields
        icp_sudo.set_param(
            'web_char_capitalize.excluded_fields_capitalize',
            self.excluded_fields_capitalize.ids
        )

        return res

    @api.model
    def get_values(self):
        """Load the many2many field values from ir.config_parameter."""
        res = super(ResConfigSettings, self).get_values()
        icp_sudo = self.env['ir.config_parameter'].sudo()

        # Load excluded models
        excluded_models = icp_sudo.get_param(
            'web_char_capitalize.excluded_models_capitalize'
        )

        # Load excluded fields
        excluded_fields = icp_sudo.get_param(
            'web_char_capitalize.excluded_fields_capitalize'
        )

        res.update(
            excluded_models_capitalize=[(6, 0, literal_eval(
                excluded_models))] if excluded_models else False,
            excluded_fields_capitalize=[(6, 0, literal_eval(
                excluded_fields))] if excluded_fields else False,
        )
        return res
