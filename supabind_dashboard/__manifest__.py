# -*- coding: utf-8 -*-
{
    'name': "Onboarder",
    'version': '1.0',
    'summary': """
        Displays the onboarder application as an embedded dashboard within Odoo.
    """,
    'description': """
        This module creates a new menu item that displays the onboarder.odoopim.com
        website in a clean, embedded iframe, providing a seamless integration
        experience without extra scrollbars or borders.
    """,
    'author': "Navabrind",
    'website': "https://navabrindsol.com",
    'category': 'Productivity',
    'depends': ['web'],

    'data': [
        'views/supabind_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'supabind_dashboard/static/src/css/custom.css',
            'supabind_dashboard/static/src/js/supabind_dashboard.js',
            'supabind_dashboard/static/src/xml/supabind_dashboard_template.xml',
        ],
    },
    
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}