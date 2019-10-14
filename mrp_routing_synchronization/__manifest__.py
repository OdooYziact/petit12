# -*- coding: utf-8 -*-
{
    'name': "MRP Routing synchronization",

    'summary': "Sync mrp routing operations and quality points",
    'author': "Yziact",
    'maintainer': '',

    # lien vers le dépôt git ou site Yziact
    'website': "http://gitlab.yziact.net/odoo/petit/addons",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Manufacturing',
    'version': '0.1',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mrp',
        'mrp_repair_order',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    # always loaded
    'data': [
        'views/mrp_routing.xml',
        'views/mrp_routing_workcenter.xml',
        'views/quality_point.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
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
