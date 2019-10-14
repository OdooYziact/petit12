# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _prepare_delivery_product(self, route_id, taxes_ids):
        """
        Créé une ligne de vente à partir d'une route
        :param route_id:
        :param taxes_ids:
        :return: new sale.order.line
        """
        delivery_product_id = route_id.delivery_method_id.product_id
        delivery_method_id = route_id.delivery_method_id

        price = delivery_method_id.fixed_price
        price = price * (1.0 + (float(delivery_method_id.margin) / 100.0))

        vals = {
            # 'order_id': self.id,
            'name': delivery_product_id.name,
            'product_uom_qty': 1,
            'product_uom': delivery_product_id.uom_id.id,
            'product_id': delivery_product_id.id,
            'price_unit': price,
            'purchase_price': price,
            'tax_id': [(6, 0, taxes_ids)],
            'is_delivery': True,
        }

        return self.new(vals)
