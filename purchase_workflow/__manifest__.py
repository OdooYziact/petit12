# -*- coding: utf-8 -*-
{
    'name': "Purchase Workflow",

    'summary': """Hold purchase order.""",

    'author': "Yziact",
    'maintainer': 'Aurelien ROY',

    # lien vers le dépôt git ou site Yziact
    'website': "http://gitlab.yziact.net/odoo/petit/addons",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.3',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'purchase',
        'purchase_requisition',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    # always loaded
    'data': [
        'views/purchase_requisition.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/res_config_settings.xml',
        'security/ir.model.access.csv'
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
