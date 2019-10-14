# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo.addons.yzi_utils.scripts.fields import get_fields_from_recordset

class SaleOrder(models.Model):
    _inherit = "sale.order"

    comment = fields.Text(string="Commentaire")

    # Methode generique pour ordonner les references client en 4 colonnes dans le XML
    def get_references_fields(self):
        return get_fields_from_recordset(self.partner_references, 4, ['name', 'value'])

    def get_workcenters_for_report(self):
        workorders = self.repair_order_id.production_id._prepare_workorders_for_report()

        wc = []

        for workorder in workorders:
            if workorder['workcenter'] not in wc:
                wc.append(workorder['workcenter'])

        return wc

    def get_stock_pickings(self):
        return self.env['stock.picking'].search([('sale_id.id', '=', self.id)], order="id")

    def get_stock_pickings_date(self):
        pickings = self.env['stock.picking'].search([('sale_id.id', '=', self.id)], order="id")

        dates = []

        for picking in pickings:
            if picking.date_done:
                dates.append(picking.date_done)
            else:
                dates.append(" ")

        return dates


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Delai pour chaque ligne du devis
    delai_line = fields.Float(string="Délai (jours)", related="product_id.sale_delay", readonly=True)


