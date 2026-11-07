# -*- coding: utf-8 -*-
{
    'name': 'Odoo PIM-concurrent login restriction',
    'version': '18.0',
    "author": "Navabrind IT",
    'summary': '',
    'description': """ OdooPIM

    """,
    'category': 'product',
    'depends': ['pim_ext'],
    'data': [
            'security/ir.model.access.csv',
            # 'views/family_attribute.xml',
            # 'views/product_attribute.xml',
            # 'views/product_brand.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'concurrent_user_restriction/static/src/js/form_controller.js',
            'concurrent_user_restriction/static/src/xml/formView.xml',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    'application': True,
    'auto_install': False,
}
