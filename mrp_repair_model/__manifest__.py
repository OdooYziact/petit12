# -*- coding: utf-8 -*-
{
    'name': "MRP repair model",
    'summary': "Ajout de modèle de réparation",
    'author': "Yziact",
    'website': "http://www.yziact.fr",

    'category': 'Repair',
    'description': """
    """,
    'version': '0.1',
    "application": False,
    "installable": True,
    # any module necessary for this one to work correctly
    'depends': [
        'mrp',
    ],

    'data': [
        'views/repair_specification.xml',
        'views/repair_model.xml',
        'security/ir.model.access.csv',
    ],
}
