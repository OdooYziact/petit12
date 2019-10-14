# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def default_get(self, fields):
        values = super(PurchaseOrder, self).default_get(fields)

        if 'default_requisition_id' in self._context:
            requisition_id = self.env['purchase.requisition'].browse(self._context.get('default_requisition_id'))
            if requisition_id.request_id:
                values.update({'request_id': requisition_id.request_id.id})

        return values

    request_id = fields.Many2one(comodel_name="material.request", required=False, default=False)

    @api.multi
    def action_hold(self):
        self.ensure_one()

        if self.request_id:
            request_line = self.env['material.request.line']
            product_to_define = self.env.ref('material_request.product_to_define')

            if any(self.order_line.mapped('product_id').filtered(lambda rec: rec.id == product_to_define.id)):
                raise ValidationError(_('Please replace product to define.'))

            # update existing lines
            for line in self.order_line.exists():
                vals = {
                    'purchase_line_id': line.id,
                    'product_qty': line.product_qty,
                    'request': 'internal_picking',
                }

                if line.product_id != line.request_line_id.product_id:
                    vals.update(line.request_line_id._prepare_product(line.product_id))
                    vals.update({'product_id': line.product_id.id})

                line.request_line_id.write(vals)

            # add new lines to request
            other_lines = self.order_line.filtered(lambda rec: not rec.request_line_id)
            for line in other_lines:
                vals = {
                    'purchase_line_id': line.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'request': 'internal_picking',
                    'is_done': True,
                }
                vals.update(request_line._prepare_product(line.product_id))
                new_request_line = request_line.create(vals)
                line.request_line_id = new_request_line.id
                self.request_id.request_line |= new_request_line

            self.order_line.mapped('request_line_id').action_done()

        return super(PurchaseOrder, self).action_hold()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_line_id = fields.Many2one(comodel_name="material.request.line", required=False, default=False)



