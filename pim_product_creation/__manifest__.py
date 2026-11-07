# -*- coding: utf-8 -*-
{
    'name': 'Product Creation',
    'version': '18.0.0.1',
    "author": "Navabrind IT Solutions",
    'summary': 'Product Creation Management',
    'description': """Product Creation Management""",
    'category': 'product',
    'depends': ['web','base','pim_ext', 'odoopim_split_widget'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'pim_product_creation/static/src/**/*.js',
            'pim_product_creation/static/src/**/*.xml',
            'pim_product_creation/static/src/**/*.css',

            'odoopim_split_widget/static/src/**/*',

        ]
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3'
}
