{
    'name': 'AI Translate',
    'version': '1.0.0',
    'category': 'Web',
    'summary': 'Translate the attributes using AI',
    'author': 'Navabrindit',
    'license': 'LGPL-3',
    'depends': [
        'pim_locales_channels','base', 'ai_enrichment',
    ],
    'data': [
        # 'views/attribute_channel_locale_inherit.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pim_ai_transulate/static/src/components/ai_translate_button.js',
            'pim_ai_transulate/static/src/components/ai_translate_button.xml',
            'pim_ai_transulate/static/src/widgets/translate_button_widget.xml',
            'pim_ai_transulate/static/src/widgets/translate_button_widget.js',

        ],
    },
    'installable': True,
    'application': False,
}
