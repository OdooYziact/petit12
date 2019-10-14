# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

# from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    margin_rate = fields.Float(compute='_compute_margin_rate', string='Taux de marge')
    total_margin_rate = fields.Float(related='margin_rate', store=True, group_operator='avg')


    def _calc_margin_rate(self):
        return self.margin / self.amount_untaxed * 100 if self.margin and self.amount_untaxed else 0.0

    @api.depends('amount_untaxed', 'margin')
    def _compute_margin_rate(self):
        """
        Calcule le taux de marge.
        :return:
        """
        for record in self:
            record.margin_rate = record._calc_margin_rate()




