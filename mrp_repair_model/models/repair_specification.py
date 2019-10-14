# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
# import pudb
#
# import logging
# _logger = logging.getLogger(__name__)


# spec_marquage_client
# marque_fabricant
# type_materiel
# puissance - KW
# vitesse - tr/min
# position
# tension - V
# intensité - A
# numero_serie
# poids - Kg
# IP


class MrpRepairSpecification(models.Model):
    _name = 'mrp.repair.specification'

    name = fields.Char(string="Name", required=False)
    active = fields.Boolean(default=True)
    common = fields.Boolean(default=False, string="Common specification")
    required = fields.Boolean(default=False, string="Required")
    description = fields.Char(string="Label", required=False)
    field_type = fields.Selection(string="Type",
                             selection=[
                                 ('char', 'Text'),
                                 ('float', 'Decimal number'),
                                 ('int', 'Integer'),
                             ],
                             required=True)

    unit = fields.Selection(string="Unit",
                             selection=[
                                 ('trmin', 'tr/min'),
                                 ('amp', 'A'),
                                 ('volt', 'V'),
                                 ('kw', 'kW'),
                                 ('kg', 'kg'),
                                 ('mm', 'mm'),
                                 ('cm', 'cm'),
                                 ('m', 'm'),
                             ],
                             required=False, default='')

    _sql_constraints = [
        ('name',
        'UNIQUE(name)',
        "The record must be unique."),
    ]

    @api.multi
    def name_get(self):
        return [(elem.id, elem.description) for elem in self]
