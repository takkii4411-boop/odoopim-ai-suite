{
    'name': 'AI -ODOOPIM- BOT',
    'version': '6.0',
    'summary': 'Integrate an AI chatbot in the Odoo web client',
    'author': 'Ragunath S M',
    'category': 'Bot',
    'depends': ['web','mail','pim_ext'],
    'data': [
        'views/bot_template.xml',
        'views/api_setting.xml',
        # 'data/file_deletion.xml'
    ],
    'controllers': ['controllers/ai_bot_controller.py'],
    'assets': {
        'web.assets_backend': [
            'web/static/lib/jquery/jquery.js',
            'ai_bot_odoopim/static/src/css/custom_footer.css',
            'ai_bot_odoopim/static/src/js/custom_footer.js',
            'ai_bot_odoopim/static/src/js/markdown-it.min.js',  # Local copy
            'ai_bot_odoopim/static/src/js/markdown-it-multimd-table.min.js',  # Local copy
        ],
        'web.assets_frontend': [
            'ai_bot_odoopim/static/src/js/markdown-it.min.js',  # Local copy
            'ai_bot_odoopim/static/src/js/markdown-it-multimd-table.min.js',  # Local copy
            'ai_bot_odoopim/static/src/js/custom_footer.js',  # Include custom JavaScript
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'uninstall_hook': 'uninstall_ai_cleanup',  # Define the uninstall hook
}
