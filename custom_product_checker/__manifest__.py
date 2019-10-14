# -*- coding: utf-8 -*-

{
    'name': "Product Validator",

    'description': """
        This module is made to control if an item master data matches difined critera*
    """,

    'author': "Yziact",
    'maintainer': 'Rémi Tabardel',

    # link to Git repository or Yziact site
    'website': "http://gitlab.yziact.net/odoo/petit/addons",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'sale',
        'base',
        'product',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml',
        'views/product.xml',
        'views/product_template_search_view.xml',
        'views/sale_order.xml',
        'wizard/wizard_popup.xml',
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
