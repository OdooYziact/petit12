# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Order Point Method:
#    - Order if the virtual stock of today is bellow the min of the defined order point
#

from odoo import  models, fields

import logging

_logger = logging.getLogger(__name__)


class StockSchedulerCompute(models.TransientModel):
    _inherit = 'stock.scheduler.compute'
    
    partner_id = fields.Many2one('res.partner', string='Vendor')