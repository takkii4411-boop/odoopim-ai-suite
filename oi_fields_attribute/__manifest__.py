# -*- coding: utf-8 -*-
{
    'name': "Field Dynamic Attributes",

    'summary': """Update field attributes from Odoo interfaces without need a custom module, Tracked Field, Tracking, Readonly""",

    'description': """
        Update field attributes from odoo interface without need a custom module
    """,

    'author': "Openinside",
    'website': "https://www.open-inside.com",
    "license": "OPL-1",
    "price" : 30,
    "currency": 'USD',    

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '18.0',

    # any module necessary for this one to work correctly
    # 'depends': ['base', 'web', 'mail'],

    # # always loaded
    # 'data': [
    #     'security/ir.model.access.csv',
    #     'view/ir_model_fields_attribute.xml',
    #     'view/ir_model_fields.xml',
    #     'view/action.xml',
    #     'view/menu.xml',
    # ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'oi_fields_attribute/static/src/field_attributes/field_attributes.js',
    #         'oi_fields_attribute/static/src/field_attributes/field_attributes.xml'
    #     ],
    # },      
    # 'external_dependencies' : {
        
    # },
    'odoo-apps' : True,
    'auto_install': True,
    'images':[
        'static/description/cover.png'
    ]     
}
