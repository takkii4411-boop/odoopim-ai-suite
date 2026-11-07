{
    'name': 'Locales and Channels',
    'version': '1.0.0',
    'category': 'Web',
    'summary': 'Combine localisation and channelization',
    'author': 'Navabrindit',
    'license': 'LGPL-3',
    'depends': ['web', 'base', 'odoo_pim_connector', 'pim_ext'],
    'data': [
        'security/ir.model.access.csv',
        'views/platform_credentials.xml',
        'views/ir_model_fields.xml',
        'views/res_users.xml',
        'views/res_config_settings.xml',
        'views/product_attributes.xml',
        'views/product_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/pim_locales_channels/static/src/*/*'
        ],
    },
    'post_init_hook': 'post_init',
    'installable': True,
    'application': False,
    'auto_install': False,
}
