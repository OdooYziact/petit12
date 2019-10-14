# -*- coding: utf-8 -*-
{
    'name': "Listes de prix par coefficient",

    'summary': """Ajout du support des listes de prix par coéfficient""",

    'author': "Yziact",
    'maintainer': 'Aurelien ROY, Victor RAVIT',
    'website': "http://www.yziact.fr",

    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends':
        [
            'base',
            'product',
        ],

    # always loaded
    'data': [
        'views/product_pricelist_item.xml',
    ],

    'installable': True,

}