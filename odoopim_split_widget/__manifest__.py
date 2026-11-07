# -*- coding: utf-8 -*-
{
    'name': "Split List and Form View",
    'summary': "List and Form view side by side",
    'description': "Odoo list-view and form-view side by side",
    'author': "Navabrind IT Solutions",
    'contributor': "Raja Mondal",
    'version': '18.0.0.1',
    'depends': ['base'],
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'views/ir_filters_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            "odoopim_split_widget/static/src/icons/*.*",
            "odoopim_split_widget/static/lib/multiselect/*.*",
            "odoopim_split_widget/static/src/components/*/*.*",
            "odoopim_split_widget/static/src/views/list/*.*",
            "odoopim_split_widget/static/src/views/tree_form_view/*.*",
            "odoopim_split_widget/static/src/views/filters/*.*",
            "odoopim_split_widget/static/src/views/fields/*/*.*",
            "odoopim_split_widget/static/src/core/pager/pager.scss",
            "odoopim_split_widget/static/src/core/l10n/*.*",
            "odoopim_split_widget/static/src/widgets/*.*",
        ],
    },
}
