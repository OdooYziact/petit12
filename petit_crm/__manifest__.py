# -*- coding:utf-8 -*-
{
    'name': "CRM custom / client PETIT",

    'description': """Modifications CRM""",

    'author': "Yziact",
    'maintainer': 'Aurelien ROY',

    # lien vers le dépôt git ou site Yziact
    'website': "http://gitlab.yziact.net/odoo/petit/addons",
    'version': '0.3',

    'category': 'Uncategorized',

    # any module necessary for this one to work correctly
    'depends': [
        'crm',
        'base_weekday',
    ],

    # always loaded
    'data': [
        'views/res_partner.xml',
        'views/geo_area.xml',
        'security/ir.model.access.csv',
    ],

    'installable': True,

    'post_init_hook': 'post_init_hook',
}
