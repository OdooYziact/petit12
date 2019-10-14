# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    delivery_manager = fields.Boolean(string="Use in delivery manager module", default=False)