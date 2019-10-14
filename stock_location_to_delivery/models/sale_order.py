# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_taxes(self, order_line_id):
        """
        Apply fiscal position
        :param order_line_id:
        :return: taxes_ids
        """
        taxes = order_line_id.product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes, order_line_id.product_id, self.partner_id).ids

        return taxes_ids


    @api.onchange('order_line')
    def _onchange_route_id(self):

        vals = self._compute_delivery()
        return {'value': vals} if vals else {}


    def _compute_delivery(self):
        """

        :return: order_line dict
        """
        order_line_env = self.env['sale.order.line']
        order_line_with_route = self.order_line.filtered(lambda x: x.route_id)

        to_add = []
        to_keep = [x.id for x in self.order_line.filtered(lambda x: not x.is_delivery)]

        # print('all: ',  [(x.id, x.name, x.is_delivery) for x in self.order_line])
        # print('to_keep: ', to_keep)

        # s'il y a des routes séléctionnées
        if order_line_with_route:
            for order_line in order_line_with_route:
                delivery_product_id = order_line.route_id.delivery_method_id.product_id

                # si l'article de livraison n'est pas dans la liste d'ajout, on le créé
                if not delivery_product_id in [x.product_id for x in to_add]:
                    taxes_ids = self._prepare_taxes(order_line)
                    new_order_line = order_line_env._prepare_delivery_product(order_line.route_id, taxes_ids)
                    to_add.append(new_order_line)

            to_keep += [x.id for x in to_add]
            # print('to_update: ', to_keep)

        # on retourne au minimum les articles qui ne sont pas des articles de livraison...
        return {'order_line': [(6, False, to_keep)]}



