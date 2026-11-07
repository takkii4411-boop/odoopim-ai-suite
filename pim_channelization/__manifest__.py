{
    'name': 'Channelization',
    'version': '1.0.0',
    'category': 'Web',
    'summary': 'Channelise products attribute fields',
    'author': 'Navabrindit',
    'license': 'LGPL-3',
    'depends': ['web','base', 'pim_locales_channels', 'odoopim_split_widget','odoo_pim_connector'],
    'data': [
        'views/product_attribute.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'pim_channelization/static/src/*/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
