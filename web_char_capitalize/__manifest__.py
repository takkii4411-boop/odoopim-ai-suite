{
    'name': 'CharField Auto Capitalize',
    'version': '1.0.0',
    'category': 'Web',
    'summary': 'Automatically capitalize first letter in char fields',
    'description': """
        This module patches the standard CharField widget to automatically
        capitalize the first letter of the input value while typing.
    """,
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'license': 'LGPL-3',
    'depends': ['web','base'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web_char_capitalize/static/src/js/char_field_capitalize.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
