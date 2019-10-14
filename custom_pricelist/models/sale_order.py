# -*- coding: utf-8 -*-

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('list_price', 'price_extra', '<')
    def _compute_product_lst_price(self):
        res = super(SaleOrder, self)._compute_product_lst_price()
        return res
