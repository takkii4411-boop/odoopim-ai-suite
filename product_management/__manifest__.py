# -*- coding: utf-8 -*-
{
    "name": "Product Management Interface",
    "version": "18.0",
    "category": "Sales",
    "author": "faOtools",
    "website": "https://faotools.com/apps/17.0/product-management-interface-827",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "product"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings.xml",
        "wizard/change_prm_category.xml",
        "wizard/update_prm_attributes.xml",
        "wizard/update_prm_followers.xml",
        "wizard/update_prm_product_type.xml",
        "wizard/update_prm_price.xml",
        "wizard/update_prm_tags.xml",
        "wizard/update_prm_optional_products.xml",
        "wizard/copy_values_from_template.xml",
        "views/product_template.xml",
        "views/menu.xml",
        "data/data.xml"
    ],
    "assets": {
        "web.assets_backend": [
                "product_management/static/src/components/product_manager/*.xml",
                "product_management/static/src/components/product_manager/*.js",
                "product_management/static/src/components/jstree_container/*.xml",
                "product_management/static/src/components/jstree_container/*.js",
                "product_management/static/src/components/product_navigation/*.xml",
                "product_management/static/src/components/product_navigation/*.js",
                "product_management/static/src/views/**/*.xml",
                "product_management/static/src/views/**/*.js",
                "product_management/static/src/views/**/*.scss"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The tool to search, select and mass update product templates. Category tree. Tags hierarchy. Attributes tree. Product kanban navigator. Remap product variants. Product catalog. Mass update product prices. Mass update product variant prices. Product server actions. Re-arrange variants. Mass products update. Update attributes. Product attributes. Change product category. Bulk update. Product mass editing.",
    "description": """For the full details look at static/description/index.html
* Features * 
- Configurable mass actions for product templates
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "148.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=86&ticket_version=17.0&url_type_id=3",
}