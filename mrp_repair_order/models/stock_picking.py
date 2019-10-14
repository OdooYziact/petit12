# -*- coding: utf-8 -*-

from odoo import api, fields, models, _




class StockPicking(models.Model):
    _inherit = 'stock.picking'

    repair_order_id = fields.Many2one(comodel_name='mrp.repair.order', default=False, string='Repair Order')