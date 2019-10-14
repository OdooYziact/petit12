# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ### ADDS ###
    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Devis', required=False)
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('retained', 'Demande de prix retenue'),
        ('waiting', 'Waiting customer'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    @api.multi
    def action_view_purchase_requisition(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Appel d'offres",
            'res_model': 'purchase.requisition',
            'res_id': self.requisition_id.id,
            'view_mode': 'form',
        }

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
    def button_confirm(self):
        self.filtered(lambda x: x.state == 'retained').write({'state': 'sent'})
        return super(PurchaseOrder, self).button_confirm()


    def _get_route_ids(self):
        """
        retourne les ids des routes à ajouter aux articles de la demande prix depuis la configuration
        :return: [ids]
        """
        add_route = self.env['ir.config_parameter'].sudo().get_param('petit_helpdesk.add_route')
        if add_route:
            return [x.route_id for x in self.env['purchase.order.route'].search([])]
        else:
            return []


    @api.multi
    def action_hold(self):
        self.ensure_one()

        # TODO: améliorer le domain de l'action xml pour ne pas raise içi
        # if self.state not in ('draft', 'sent'):
        #     raise UserError("Vous ne pouvez retenir une demande de prix que si celle-ci est encore en brouillon ou vient d'être envoyée.")

        # récupération des routes à ajouter aux produits composant le demande de prix
        route_ids = self._get_route_ids()

        # ajoute le fournisseur et le PA aux articles de la demande de prix
        self._add_supplier_to_product()

        self.state = 'retained'

        if self.requisition_id:
            # cancel other purchase order
            others_po = self.requisition_id.mapped('purchase_ids').filtered(lambda r: r.id != self.id)
            others_po.button_cancel()
            self.requisition_id.action_done()

        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def action_view_order(self):
        action = {
            "type": "ir.actions.act_window",
            "name": _('Purchase order'),
            "res_model": "purchase.order",
            "res_id": self.order_id.id,
            "view_type": 'form',
            "views": [[False, "form"], [False, "tree"]],
            "target": 'current',
        }

        return action




