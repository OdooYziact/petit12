# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line']

    is_validated = fields.Boolean(related="product_id.is_validated")

    def check_item_mdm(self):
        return self.product_id.action_check()
