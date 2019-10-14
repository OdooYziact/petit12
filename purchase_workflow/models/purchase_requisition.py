# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'
    _description = "Appel d'offres"


    sale_order_id = fields.Many2one(comodel_name="sale.order", required=False, default=False)

    @api.multi
    def get_purchase_order(self):
        pr = self.env['purchase.order']
        for purchase in self:
           pr |= purchase.purchase_ids
        return pr

    @api.multi
    def action_view_sale_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Devis",
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
        }

    @api.multi
    def action_create_purchase_order(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': "Demande de prix",
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'context': {
                'default_requisition_id': self.id
            }
        }
        if self.sale_order_id:
            action['context']['default_sale_order_id'] = self.sale_order_id.id
        return action



class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    name = fields.Text(string='Description', required=True)


    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(PurchaseRequisitionLine, self)._onchange_product_id()

        if self.product_id:
            self.name = self.product_id.display_name
            if self.product_id.description_purchase:
                self.name += '\n' + self.product_id.description_purchase


    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        vals = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name, product_qty, price_unit,
                                                                                 taxes_ids)
        if self.requisition_id:
            if vals.get('name', False):
                vals['name'] = self.name

        return vals
