# -*- coding: utf-8 -*-
{
    'name': "Material Request",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Yziact",
    'maintainer': 'Aurelien ROY',

    # lien vers le dépôt git ou site Yziact
    'website': "http://gitlab.yziact.net/odoo/global/material_request",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1.0',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'purchase',
        'purchase_requisition',
        'purchase_workflow',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/ir_sequence.xml',
        'wizard/wizard.xml',
        'wizard/purchase_order_create.xml',
        'views/material_request.xml',
        'views/material_request_line.xml',
        'views/purchase_order.xml',
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
