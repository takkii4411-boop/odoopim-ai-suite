# -*- coding: utf-8 -*-
{
    'name': 'Product Association Management',
    'version': '18.0.1.0.0',
    'category': 'Sales/PIM',
    'summary': 'Manage product associations with flexible types - Akeneo PIM Style',
    'description': """
        Product Association Management for Odoo PIM
        =============================================

        This module provides a modern, flexible product association system:

        Key Features:
        -------------
        * Define custom association types (Upsell, Cross-sell, Pack, Substitution, etc.)
        * Link products with different association types
        * Modern UI inspired by Akeneo PIM
        * Easy-to-use association management interface
        * Type selector with "Add Associations" button
        * Beautiful dialog with product search and filters
        * 3-column kanban view for associated products
        * Query-optimized controller for performance
        * Pre-selected products in dialog
        * Responsive design

        Technical Highlights:
        --------------------
        * OWL Components (Odoo 18)
        * Raw SQL queries for performance
        * Custom widgets and templates
        * Professional SCSS styling
        * Clean separation of concerns

        Perfect for:
        -----------
        * E-commerce product relationships
        * PIM systems
        * Product catalog management
        * Cross-selling and upselling strategies
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'web',
        'pim_ext',  # Your existing PIM extension module
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/product_association_type_data.xml',

        # Views
        'views/product_association_type_views.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # JavaScript
            'odoo_pim_association/static/src/js/association_widget.js',

            # XML Templates
            'odoo_pim_association/static/src/xml/association_templates.xml',

            # SCSS
            'odoo_pim_association/static/src/scss/association_dialog.scss',
            'odoo_pim_association/static/src/scss/association_kanban.scss',
            'odoo_pim_association/static/src/scss/confirmation_dialog.scss',
        ],
    },
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 0.00,
    'currency': 'USD',
}
