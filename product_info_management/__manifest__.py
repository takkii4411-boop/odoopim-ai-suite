# -*- coding: utf-8 -*-
{
    'name': 'Product information Management',
    'version': '18.0',
    "author": "Navabrind IT Solutions",
    'summary': 'Product information Management',
    'description': """
        Product information Management
    """,
    'category': 'product',
    'depends': ['base','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/pim_views.xml',
        'views/product_views.xml',
        'views/pim_attribute_views.xml',
        'views/pim_attribute_group_views.xml',
        'views/pim_family_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license':'LGPL-3'
}
