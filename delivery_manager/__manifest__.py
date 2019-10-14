# -*- coding: utf-8 -*-
{
    'name': "Delivery Manager",

    'description': """
        Manage and schedule delivery order.
    """,

    'author': "Yziact",
    'maintainer': 'Aurelien ROY',

    # lien vers le dépôt git ou site Yziact
    'website': "http://gitlab.yziact.net/odoo/global/delviery_manager",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'stock_dropshipping',
        'web_digital_sign',
        'base_weekday',
        'petit_crm',
        'delivery',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    # always loaded
    'data': [
        'data/data.xml',
        'views/templates.xml',
        'views/stock_picking.xml',
        'views/stock_picking_type.xml',
        'views/delivery_carrier.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False, 

    # Hooks for module installation/uninstallation, their value should be a string
    # representing the name of a function defined inside the module's __init__.py.
    # 'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    # 'uninstall_hook': '',
}
