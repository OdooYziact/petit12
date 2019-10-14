# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'


    request_id = fields.Many2one(comodel_name="material.request", required=False, default=False)


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'


    request_line_id = fields.Many2one(comodel_name="material.request.line", required=False, default=False)

    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        res = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name, product_qty, price_unit, taxes_ids)

        if self.request_line_id:
            res.update({
                'request_line_id': self.request_line_id.id,
            })

        return res

