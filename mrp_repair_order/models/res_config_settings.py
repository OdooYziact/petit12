# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_picking_type_in = fields.Many2one(comodel_name='stock.picking.type', default_model='mrp.repair.order',
                                              string='Default picking type for move in')
    default_picking_type_out = fields.Many2one(comodel_name='stock.picking.type', default_model='mrp.repair.order',
                                              string='Default picking type for move out')
