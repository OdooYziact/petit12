# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class PartnerReferencesData(models.Model):
    _inherit = "partner.references.data"

    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=False)

    @api.model
    def get_vals_from_origin(self, origin, origin_id):
        vals = super(PartnerReferencesData, self).get_vals_from_origin(origin, origin_id)

        if origin == 'sale.order':
            vals['sale_order_id'] = origin_id.id

        return vals