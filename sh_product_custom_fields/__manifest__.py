# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Product Custom Fields",

    "author": "Softhealer Technologies",

    "license": "OPL-1",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "18.0",

    "category": "Extra Tools",

    "summary": "Product Custom Fields Product Dynamic Field Add Product New Field Make Product Dynamic Fields Create Product New Field  Assign Custom Fields Edit Product Custom Field Update Product Custom Field Odoo",

    "description": """This module useful to create dynamic fields in the product templates and variants without any technical knowledge. Easy to use. Specify basic things and fields added in the form view.""",

    "depends": ['sale_management'],

    "data": [
        "data/product_template_custom_field_group.xml",
        "security/ir.model.access.csv",
        "views/product_tab.xml",
        "views/template_tab.xml",
        "views/product_template.xml",
        "views/product_product.xml",
    ],

    "images": ["static/description/background.png", ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "35",
    "currency": "EUR"
}
