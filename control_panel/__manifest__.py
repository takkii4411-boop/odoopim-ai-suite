# -*- coding: utf-8 -*-
{
    'name': 'PIM Control Panel',
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': '',
    'description': """ OdooPIM For MisterArt

    """,
    'category': 'product',
    'depends': ['pim_ext'],
    'data': [
        'views/product_template.xml'
    ],
    'assets': {
        'web.assets_backend': [
            # 'pim_ext/static/src/css/view_button.css',
            'control_panel/static/src/scss/control_panel.scss',
            # 'pim_ext/static/src/css/custom.scss',
            # 'pim_ext/static/src/css/kanban.scss',
            'control_panel/static/src/js/rightpanel_list.js',
            # 'control_panel/static/src/js/search_model.js',
            # 'control_panel/static/src/js/navigation.js',
            # 'control_panel/static/src/xml/navigation.xml',
            # 'control_panel/static/src/jstree_container/jstree_container.js',
            # 'control_panel/static/src/jstree_container/jstree_container.xml',
            'control_panel/static/src/xml/rightpanel_list.xml',
            # 'control_panel/static/src/js/rightpanel_kanban.js',
            # 'control_panel/static/src/xml/rightpanel_kanban.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
