# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ### ADDS ###
    helpdesk_ticket_id = fields.Many2one(comodel_name='helpdesk.ticket', string='Ticket', required=False, default=False)

    ### ACTION ###
    @api.multi
    def action_view_helpdesk_ticket(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Ticket",
            'res_model': 'helpdesk.ticket',
            'res_id': self.helpdesk_ticket_id.id,
            'view_mode': 'form',
        }

    # action_select_request
    @api.multi
    def action_hold(self):
        """
        Passe la demande de prix à l'état retenue, annule les autres demandes ratachées à l'appel d'offre,
        marque celui-ci comme fait et met à jour le devis client
        :return: action or Boolean
        """

        self.ensure_one()

        if self.helpdesk_ticket_id:
            action = True
            from_ticket = False

            # récupération du context inséré dans l'action xml
            origin = self.env.context.get('origin', False)
            if origin == 'ticket':
                from_ticket = True

            # récupération des routes à ajouter aux produits composant le demande de prix
            route_ids = self._get_route_ids()

            # create sale order if not exist
            if from_ticket and not self.sale_order_id:
                so = self.helpdesk_ticket_id.create_sale_order()
                self.sale_order_id = so

                if self.requisition_id:
                    self.requisition_id.sale_order_id = so

                # update sale order with current lines
                order_lines = []
                sale_order_line_env = self.env['sale.order.line']

                for line in self.order_line:

                    if route_ids:
                        line.product_id.product_tmpl_id.sudo().update({'route_ids': [x.id for x in route_ids]})

                    new_order_line = sale_order_line_env.create({
                        'order_id': self.sale_order_id.id,
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'purchase_price': line.price_unit,
                        'product_uom': line.product_uom.id,
                        'product_uom_qty': line.product_qty,
                    })
                    order_lines.append(new_order_line)

                to_add = [line.id for line in order_lines]
                to_keep = self.sale_order_id.order_line.filtered(lambda x: x.product_id.id not in [line.product_id.id for line in order_lines])
                to_update = to_add + [x.id for x in to_keep]

                # replace all, keep diff and add news
                self.sale_order_id.update({
                    'order_line': [(6, False, to_update)]
                })

                action = {
                    'type': 'ir.actions.act_window',
                    'name': "Devis",
                    'res_model': 'sale.order',
                    'res_id': self.sale_order_id.id,
                    'view_mode': 'form',
                }

                res = super(PurchaseOrder, self).action_hold()
                return action

        return super(PurchaseOrder, self).action_hold()







