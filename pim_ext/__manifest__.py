# -*- coding: utf-8 -*-
{
    'name': 'OdooPIM',
    'version': '18.0.0.1',
    "author": "Navabrind",
    'summary': 'Dealing with product information management',
    'description': """
        Project Information Management
    """,
    'category': 'product',
    'depends': ['web', 'base', 'sale', 'product',
                'stock', 'website_sale', 'web_hierarchy', 'mail',
                'odoopim_split_widget', 'web_studio',
                'odoo_pim_connector',
                'stock_barcode', 'spreadsheet_dashboard'],
    'data': [
        'security/group_security.xml',
        'security/ir.model.access.csv',
        'data/general_attributes_data.xml',
        'data/default_attributes.xml',
        'data/sequence.xml',
        'data/server_actions.xml',
        'data/pim_category_data.xml',
        'wizard/product_view.xml',
        'wizard/delete_family.xml',
        'wizard/mass_edit_view.xml',
        'wizard/category_wizard.xml',
        'wizard/family_wizard.xml',
        'views/pim_attribute_split_views.xml',
        'views/pim.xml',
        'views/product_attribute.xml',
        'views/family_attribute.xml',

        'wizard/attribute_group_wizard_views.xml',
        'wizard/attribute_wizard_views.xml',
        'wizard/attribute_variant_wizard_views.xml',
        'wizard/product_create_wizard.xml',

        'views/pim_category_views.xml',
        'views/pim_channels_views.xml',
        'views/brand.xml',
        'views/product_select_family.xml',
        'views/general_attributes.xml',
        'views/supplier.xml',
        'views/pim_attribute_group_split_views.xml',
        'views/menuitems.xml',
        'views/product_creation_views.xml',
        'views/product_product.xml',
        'views/res_config_settings.xml',
        'views/pim_product_publish_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pim_ext/static/src/css/product_kanban.scss',
            'pim_ext/static/src/css/custom_style.scss',
            'pim_ext/static/src/css/custom_style.css',

            # 'pim_ext/static/src/js/chatter_position.js',
            # 'pim_ext/static/src/js/create_button.js',
            'pim_ext/static/src/xml/create_button.xml',
            'pim_ext/static/src/xml/video_selector.xml',
            'pim_ext/static/src/js/video_selector.js',
            'pim_ext/static/src/js/one2many_widget.js',
            'pim_ext/static/src/js/image_dnd.js',
            # 'pim_ext/static/src/js/view_button.js',
            # 'pim_ext/static/src/js/dis_button.js',
            # 'pim_ext/static/src/xml/view_button.xml',
            'pim_ext/static/src/js/category_tree.js',
            'pim_ext/static/src/js/progressbar_field.js',
            # 'pim_ext/static/src/js/animated_number_custom.js',
            'pim_ext/static/src/xml/progressbar_widget_extended.xml',
            'pim_ext/static/src/js/tree_form_controller.js',
            'pim_ext/static/src/xml/category_tree_view.xml',
            'pim_ext/static/src/xml/list_view.xml',
            'pim_ext/static/src/xml/image_dnd.xml',

            'pim_ext/static/src/widgets/go_back_btton_widget.js',
            'pim_ext/static/src/widgets/go_back_button.xml',
            'pim_ext/static/src/widgets/Field.js',
            'pim_ext/static/src/widgets/Field.xml',

            'pim_ext/static/src/widgets/many2one_embedded_form/embedded.xml',
            'pim_ext/static/src/widgets/many2one_embedded_form/many2one_form.js',

            'pim_ext/static/src/widgets/one2many_list_kanban/list_and_kanban.js',
            'pim_ext/static/src/widgets/one2many_list_kanban/list_kanban.xml',

            'pim_ext/static/src/widgets/color_widget/colors.js',
            'pim_ext/static/src/widgets/color_widget/color.xml',
            'pim_ext/static/src/widgets/color_widget/color.css',

            'pim_ext/static/src/widgets/boolean_radio/bool_radio.js',
            'pim_ext/static/src/widgets/boolean_radio/bool_radio.xml',

            # JavaScript files (loaded in correct order)
            'pim_ext/static/src/views/attribute_split_view/attribute_split_controller.js',
            'pim_ext/static/src/views/attribute_split_view/attribute_split_renderer.js',
            'pim_ext/static/src/views/attribute_split_view/attribute_split_view.js',

            # XML template
            'pim_ext/static/src/views/attribute_split_view/attribute_split_view.xml',

            # SCSS styling
            'pim_ext/static/src/views/attribute_split_view/attribute_split_view.scss',

            'pim_ext/static/src/js/enhanced_media_upload_widget.js',
            'pim_ext/static/src/xml/enhanced_media_upload_widget.xml',

            'pim_ext/static/src/widgets/varaint_creation/product_variant.js',
            'pim_ext/static/src/widgets/varaint_creation/product_variant.xml',
            'pim_ext/static/src/widgets/varaint_creation/action.xml',
            'pim_ext/static/src/widgets/varaint_creation/action.js',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    'application': True,
    'auto_install': False,
}
