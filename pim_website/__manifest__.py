{
    'name': 'PXM Shop',
    'version': '1.0.0',
    'summary': 'Sample PXM fields and custom shop page snippet',
    'category': 'Website',
    'author': 'Generated Sample',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'website_sale', 'product', 'pim_ext', 'odoo_pim_association'],
    'data': [
        'report/product_report.xml',

        'data/menu.xml',
        'views/product_shop_page.xml',
        'views/ecommerce_details_page.xml',
        'views/pager.xml',
        'views/opptional_alternative_product_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # CSS
            'pim_website/static/src/css/custom_style.css',
            'pim_website/static/src/css/custom_style_1.css',
            'pim_website/static/src/css/product_detail_page.css',
            'pim_website/static/src/css/new_shop_page.css',
            'pim_website/static/src/css/pager.css',
            'pim_website/static/src/css/associate_product.css',

            # JS
            'pim_website/static/src/js/product_detail_page.js',
            'pim_website/static/src/js/shop_page.js',
            'pim_website/static/src/js/catalogue.js',
            'pim_website/static/src/js/pim_website.js',
            'pim_website/static/src/js/opptional_alternative_product.js',

            #xml
            # 'pim_website/static/src/xml/report.xml'

        ],
        'website.assets_editor': [
            # 'pim_website/static/src/js/pim_website.js',
        ],
    },
    'installable': True,
    'application': False,
}
