# -*- coding: utf-8 -*-

import time

from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)

        if order.repair_order_id:
            invoice.write({'repair_order_id': order.repair_order_id.id})

        return invoice