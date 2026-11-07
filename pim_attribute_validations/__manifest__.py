{
    'name': 'PIM Attribute Validations',
    'version': '1.0',
    'author': 'Your Name',
    'license': 'LGPL-3',
    'summary': 'Adds validation parameters to product attributes',
    'depends': ['pim_ext', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/image_attribute_type_data.xml',
        'views/product_attribute_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pim_attribute_validations/static/src/Field.js',
            'pim_attribute_validations/static/src/Field.xml',
            'pim_attribute_validations/static/src/field_validations.scss'
        ],
    },
    'installable': True,
}
