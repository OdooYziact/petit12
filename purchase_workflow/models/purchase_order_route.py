# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrderRoute(models.Model):
    """
    Gestion des routes ajoutées aux articles lors de la validation des demandes de prix.
    """
    _name = 'purchase.order.route'
    _description = 'Routes'


    route_id = fields.Many2one(comodel_name="stock.location.route", string="Route", required=True)
    name = fields.Char(related="route_id.name")

    _sql_constraints = [
         ('route_id',
          'unique(route_id)',
          _('Choose another value - it has to be unique!'))
    ]

