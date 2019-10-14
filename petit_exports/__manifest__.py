# -*- coding: utf-8 -*-
{
    'name': "Export custom / client PETIT",

    'summary': """Exports""",

    'author': "Yziact",
    'maintainer': 'C. CAPARROS',

    'website': "http://yziact.fr/",


    'category': 'Finance',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'sale',
        'purchase'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/export_account_invoice.xml',
        'views/account_invoice_export.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
