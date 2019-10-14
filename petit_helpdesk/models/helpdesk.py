# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    partner_id = fields.Many2one('res.partner', required=True, default=False)

    partner_contact_id = fields.Many2one('res.partner', string='Contact', readonly=True, required=False,
                                         states={'draft': [('readonly', False)]},
                                         help="Contact")

    sale_order_count = fields.Integer(string='# of Sale orders', compute='_compute_sale_order', readonly=True)
    sale_order_ids = fields.One2many("sale.order", string='Sale Order', compute="_compute_sale_order", readonly=True)

    purchase_requisition_count = fields.Integer(string='# of Sale orders', compute='_compute_purchase_requisition', readonly=True)
    purchase_requisition_ids = fields.One2many("purchase.requisition", string='Purchase Requisition', compute="_compute_purchase_requisition", readonly=True)

    purchase_order_count = fields.Integer(string='# of Sale orders', compute='_compute_purchase_order', readonly=True)
    purchase_order_ids = fields.One2many("purchase.order", string='Purchase Requisition', compute="_compute_purchase_order", readonly=True)

    repair_order_count = fields.Integer(string='# of Repair Order', compute='_compute_repair_order', readonly=True)
    repair_order_ids = fields.One2many("mrp.repair.order", string='Repair Order', compute="_compute_repair_order", readonly=True)

    ### COMPUTE ###

    def _compute_sale_order(self):
        for ticket in self:
            ticket.sale_order_ids = self.env['sale.order'].search([('helpdesk_ticket_id', '=', ticket.id)])
            ticket.sale_order_count = len(ticket.sale_order_ids)

    def _compute_purchase_requisition(self):
        for ticket in self:
            ticket.purchase_requisition_ids = self.env['purchase.requisition'].search([('helpdesk_ticket_id', '=', ticket.id)])
            ticket.purchase_requisition_count = len(ticket.purchase_requisition_ids)

    def _compute_purchase_order(self):
        for ticket in self:
            ticket.purchase_order_ids = self.env['purchase.order'].search([('helpdesk_ticket_id', '=', ticket.id)])
            ticket.purchase_order_count = len(ticket.purchase_order_ids)

    def _compute_repair_order(self):
        for ticket in self:
            ticket.repair_order_ids = self.env['mrp.repair.order'].search([('helpdesk_ticket_id', '=', ticket.id)])
            ticket.repair_order_count = len(ticket.repair_order_ids)

    ### ACTION ###

    @api.multi
    def button_create_sale_order(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': "Nouveau devis",
            'res_model': 'sale.order',
            'view_mode': 'form',
            'context': {'search_default_is_open': True,
                        'search_default_partner_id': self.partner_id.id,
                        'default_helpdesk_ticket_id': self.id}
        }

        if self.partner_contact_id:
            action['context']['default_partner_contact_id'] = self.partner_contact_id.id

        return action

    # @api.multi
    # def button_create_repair_order(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': "Nouvelle réparation",
    #         'res_model': 'mrp.repair.order',
    #         'view_mode': 'form',
    #         'context': {'search_default_is_open': False,
    #                     'search_default_partner_id': self.partner_id.id,
    #                     'default_helpdesk_ticket_id': self.id}
    #     }


    @api.multi
    def action_view_repair_order(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Réparation',
            'res_model': 'mrp.repair.order',
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'context': {'search_default_is_open': True,
                        'search_default_partner_id': self.partner_id.id,
                        'default_helpdesk_ticket_id': self.id}
        }
        if self.partner_contact_id:
            action['context']['default_partner_contact_id'] = self.partner_contact_id.id

        return action

    @api.multi
    def action_view_sale_order(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Devis',
            'res_model': 'sale.order',
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'context': {
                'search_default_is_open': True,
                'search_default_partner_id': self.partner_id.id,
                'default_helpdesk_ticket_id': self.id
            }
        }

        if self.partner_contact_id:
            action['context']['default_partner_contact_id'] = self.partner_contact_id.id

        return action

    @api.multi
    def action_view_purchase_requisition(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Appel d'offres",
            'res_model': 'purchase.requisition',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'context': {
                'search_default_is_open': True,
                'default_helpdesk_ticket_id': self.id
            }
        }

    @api.multi
    def action_view_purchase_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Demande de prix",
            'res_model': 'purchase.order',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'context': {
                'search_default_is_open': True,
                'default_helpdesk_ticket_id': self.id
            }
        }