# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    helpdesk_ticket_id = fields.Many2one(comodel_name="helpdesk.ticket", string="Ticket", required=False, default=False)

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
        action = super(SaleOrder, self).action_view_purchase_requisition()

        if self.helpdesk_ticket_id:
            action['context'].update({
                'default_helpdesk_ticket_id': self.helpdesk_ticket_id.id,
            })

        return action

