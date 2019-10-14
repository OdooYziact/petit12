# -*- coding: utf-8 -*-


# from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError



class MaterialRequestLine(models.Model):
    _inherit = 'material.request.line'

    @api.multi
    def _prepare_for_sale(self):
        self.ensure_one()

        vals = {
            'product_id': self.product_id,
            'description': "%s\n%s" % (self.product_id.name_get()[0][1], self.product_id.description_sale if self.product_id.description_sale else ''),
            'product_uom_qty': self.product_qty,
            'product_uom': self.product_uom,
            'request_line_id': self.id,
        }

        if self.purchase_line_id:
            vals['price_unit'] = self.price_unit

        return vals