# -*- coding:utf-8 -*-
{
    'name': "stock_location_to_delivery",

    'summary': """ Routes/Méthodes de livraison""",

    'description': """ Routes/Méthodes de livraison à la ligne (devis)""",

    'author': "Yziact",
    'maintainer': '',

    # lien vers le dépôt git ou site Yziact
    'website': "http://gitlab.yziact.net/odoo/global/stock_location_to_delivery",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'web',
        'delivery',
        'sale_stock'
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    # always loaded
    'data': [
        'data/data.xml',
        'views/stock_location_route.xml',
        'views/sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,

    # Hooks for module installation/uninstallation, their value should be a string
    # representing the name of a function defined inside the module's __init__.py.
    # 'pre_init_hook': '',
    # 'post_init_hook': '',
    # 'uninstall_hook': '',
}
