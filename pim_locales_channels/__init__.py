from . import models

import logging

_logger = logging.getLogger(__name__)


def prepare_field_vals():
    """Prepare the field values for global translation model
    (writing into one2many field in ir.model)"""
    return [
        (0, 0,
         {'name': 'x_res_model', 'field_description': 'Declaration Model Name', 'ttype': 'char', 'required': True}),
        (0, 0, {'name': 'x_res_id', 'field_description': 'Record ID', 'ttype': 'many2one_reference'}),
        (0, 0, {'name': 'x_field_name', 'field_description': 'Field Name', 'ttype': 'char'}),
        (0, 0, {'name': 'x_ttype', 'field_description': 'Field Type', 'ttype': 'selection'}),
        (0, 0, {'name': 'x_lang_id', 'field_description': 'Language', 'ttype': 'many2one', 'relation': 'res.lang'}),
        (0, 0, {'name': 'x_value', 'field_description': 'Value', 'ttype': 'char', 'required': True}),
    ]


def init_platform_models(env):
    """call the create_platform_model method to check and
    create new model for platform credentials"""
    env["platform.credentials"].sudo().search([('is_active', '=', True)]).create_platform_model()


def init_global_translation_model(env):
    """create the global translation model dynamically to save other
    models data that is not work with channels"""
    model = env['ir.model'].sudo()
    gt_model = model.search([('model', '=', 'x_global_locale_save')])
    if not gt_model:
        model.create([{
            'name': 'x_global_locale_save',
            'model': 'x_global_locale_save',
            'field_id': prepare_field_vals()
        }])
        _logger.info("Created new model for x_global_locale_save")
    else:
        _logger.info("x_global_locale_save model already exist in system")


def post_init(env):
    """(Works after installing the module)
    Init the models for translation purpose by channels
    and also one model for global translation"""
    init_platform_models(env)
    init_global_translation_model(env)
