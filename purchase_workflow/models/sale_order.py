# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    purchase_requisition_count = fields.Integer(string='# of Sale orders', compute='_get_purchase_requisition',
                                                readonly=True, groups="purchase.group_purchase_manager")
    purchase_requisition_ids = fields.One2many("purchase.requisition", string='Purchase Requisition',
                                               compute="_get_purchase_requisition", readonly=True,
                                               groups="purchase.group_purchase_manager")
    purchase_order_count = fields.Integer(string='# of Purchase orders', compute='_get_purchase_order', readonly=True,
                                          groups="purchase.group_purchase_manager")
    purchase_order_ids = fields.One2many("purchase.order", compute="_get_purchase_order", readonly=True,
                                         groups="purchase.group_purchase_manager")

    @api.multi
    @api.depends('state')
    def _get_purchase_order(self):
        for order in self:
            order.purchase_order_ids = self.env['purchase.order'].search(['|', ('origin', 'like', order.name), ('id', 'in', [po.id for po in order.purchase_requisition_ids.get_purchase_order()])])
            order.purchase_order_count = len(order.purchase_order_ids)

    @api.multi
    def _get_purchase_requisition(self):
        for order in self:
            order.purchase_requisition_ids = self.env['purchase.requisition'].search([('sale_order_id', '=', order.id)])
            order.purchase_requisition_count = len(order.purchase_requisition_ids)

    @api.multi
    def button_create_purchase_requisition(self):
        lines = self._order_lines_to_requisition_lines()

        return {
            'type': 'ir.actions.act_window',
            'name': "Créer un appel d'offres",
            'res_model': 'purchase.requisition',
            'view_mode': 'form',
            'context': {

                'default_line_ids': lines,
                'default_sale_order_id': self.id,
                'default_origin': self.name,
            }
        }

    def _order_lines_to_requisition_lines(self):
        lines = []
        for line in self.order_line:
            lines.append({
                'name': line.name,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'qty_ordered': line.product_uom_qty,
                'product_qty': line.product_uom_qty,
            })
        return lines


    @api.multi
    def action_view_purchase_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Commandes d'achat",
            'res_model': 'purchase.order',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'context': {
                'default_origin': self.name,
            }
        }

    @api.multi
    def action_view_helpdesk_ticket(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Ticket",
            'res_model': 'helpdesk.ticket',
            'res_id': self.helpdesk_ticket_id.id,
            'view_mode': 'form',
        }

    @api.multi
    def action_view_purchase_requisition(self):
        lines = self._order_lines_to_requisition_lines()

        return {
            'type': 'ir.actions.act_window',
            'name': "Appel d'offres",
            'res_model': 'purchase.requisition',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('sale_order_id', '=', self.id)],
            'context': {
                'default_line_ids': lines,
                'default_sale_order_id': self.id,
                'default_origin': self.name,
            }
        }

