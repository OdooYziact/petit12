# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
# from odoo.exceptions import UserError, ValidationError

# import logging
# _logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    operation_id = fields.Many2one(comodel_name="mrp.routing.workcenter", required=False, default=False)
    request_line_id = fields.Many2one(comodel_name="material.request.line")

    ### INHERIT ###
    @api.depends('order_id.state')
    def _compute_invoice_status(self):
        super(SaleOrderLine, self)._compute_invoice_status()

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.order_id.state == 'repair_confirmed' and not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        super(SaleOrderLine, self)._get_to_invoice_qty()

        for line in self:
            if line.order_id.state == 'repair_confirmed':
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced