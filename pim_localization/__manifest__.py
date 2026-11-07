{
    'name': 'Localization',
    'version': '1.0.0',
    'category': 'Web',
    'summary': 'Localize products attribute fields',
    'author': 'Navabrindit',
    'license': 'LGPL-3',
    'depends': ['web', 'base', 'pim_locales_channels', 'odoopim_split_widget'],
    'data': [
        'views/product_attributes.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pim_localization/static/src/*/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
