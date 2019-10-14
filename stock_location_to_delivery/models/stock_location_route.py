# -*- coding: utf-8 -*-

from odoo import models, fields, api, _



class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    delivery_method_id = fields.Many2one('delivery.carrier', 'Méthode de livraison', required=False)


    @api.onchange('sale_selectable')
    def preturn_null(self): 
        if not self.sale_selectable:
            self.delivery_method_id = None



