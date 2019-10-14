# -*- coding: utf-8 -*-
{
    'name': "Sale Order custom - client PETIT",

    'summary': """Sale Order custom""",

    'description': """""",

    'author': "Yziact",
    'maintainer': 'Aurelien ROY',

    # lien vers le dépôt git ou site Yziact
    'website': "http://gitlab.yziact.net/odoo/petit/addons",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sale',
    'version': '0.3',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'sale_management',
        'sale_stock',
        'purchase',
        'partner_references',
        'mrp_repair_order',
        'sale_order_dates',
        'custom_sales_margin',
        'delivery_manager',
    ],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/data.xml',
        'views/sale_order.xml',
        'views/account_invoice.xml',
        'views/res_partner.xml',
        'views/purchase_order.xml',
        'reports/sale_ca_report.xml',
        'views/res_config_settings_views.xml',
        # 'views/mail_compose_message_view.xml',
        # 'reports/sale_report_templates.xml',
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
