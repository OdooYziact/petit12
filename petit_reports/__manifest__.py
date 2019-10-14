# -*- coding:utf-8 -*-
{
    'name': "Reports",

    'summary': """ Transformation et ajout de reports """,

    'description': """ BL, BC/devis, Factures, réparations """,

    'author': "Yziact",
    'maintainer': 'C. CAPARROS',

    'website': "http://gitlab.yziact.net/odoo/petit/addons",

    'category': 'Other',
    'version': '0.2',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'sale',
        'stock',
        'account',
        'purchase',
        'petit_sale_order',

    ],

    'data': [
        'reports/header_footer.xml',
        'reports/sale_order.xml',
        'reports/sale_order_fix.xml',
        'reports/stock_picking2.xml',
        'reports/account_invoice.xml',
        'reports/mrp_repair_order_expertise.xml',
        'reports/mrp_repair_order_report_header.xml',
        'reports/purchase_order.xml',
        'reports/mrp_repair_order_etiquette.xml',
        'reports/sale_order_bilan.xml',
        'reports/mrp_repair_order_bilan.xml',
        'reports/mrp_repair_order_etiquette_dymo.xml',
        'reports/report_templates.xml',

        'views/sale_order.xml',
        'views/res_config_settings.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
