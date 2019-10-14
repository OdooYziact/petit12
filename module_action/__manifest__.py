# -*- coding: utf-8 -*-
{
    'name': "Actions commerciales",

    'summary': """Actions commerciales""",

    'description': """Module de gestion des actions commerciales menées dans le cadre d'une CRM.""",

    'author': "Yziact",
    'website': "http://gitlab.yziact.net/odoo/global/module_action",

    'category': 'Test',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends':
        [
            'base',
            'crm',
            'mail',
            'calendar',
            'sale',
            # 'sales_team',
            #'purchase',
        ],

    # always loaded
    'data': [
        'views/mail_activity.xml',
        'views/res_partner.xml',
        'views/calendar_event.xml',

        # 'views/account_invoice.xml',
        # 'views/stock_picking.xml',
        # 'views/sale_order.xml',
        # 'views/purchase_order.xml',
        # 'views/crm_lead.xml',
    ],
    'qweb': [
        'static/src/xml/mail_activity_inherit.xml',
    ],
}
