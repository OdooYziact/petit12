# -*- coding:utf-8 -*-
{
    'name': "Stock scheduler",

    'summary': """ Stock scheduler/partner""",

    'description': """ Stock scheduler/partner """,

    'author': "Itgwana",
    'website': "http://www.itgwana.com",

    'version': '0.1',

    "category": "Stock",

    # any module necessary for this one to work correctly
    'depends': [
        'stock',
        'purchase',
        'stock_account'
    ],

    # always loaded
    'data': [
        'wizard/stock_scheduler.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
