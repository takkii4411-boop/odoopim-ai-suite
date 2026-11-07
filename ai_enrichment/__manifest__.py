{
    'name': 'AI Enrichment',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Manage AI Providers and Models for Enrichment',
    'depends': ['base', 'product','pim_ext'],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_enrichment_config.xml',
        'views/ai_enrichment_wizard.xml',
        'views/dashboard_enrichment_config.xml',
        'views/ai_enrichment_queue_log_views.xml',
        'views/menus.xml',
        'data/ir_cron_data.xml',
        'data/sequence.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "ai_enrichment/static/src/css/enrich_update.css",
            "ai_enrichment/static/src/js/production_dashboard.js",
            "ai_enrichment/static/src/js/wizard_loader.js",
            "ai_enrichment/static/src/xml/dashboard_template.xml",
            # "ai_enrichment/static/src/description/icon.png",
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
