{
    'name': 'PIM Approval Workflow',
    'version': '1.0',
    'summary': 'PIM Approval Workflow',
    'description': """
        This module implements an approval workflow for product information management (PIM) in Odoo.
        It includes role-based transitions, centralized workflow configuration, and notifications.
    """,
    'author': "Navabrind IT Solutions",
    'contributor': "Raja Mondal",
    'category': 'Productivity',
    'depends': ['base', 'product', 'mail', 'pim_ext'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/pim_workflow_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}