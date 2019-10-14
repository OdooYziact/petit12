# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
# import pudb
#
# import logging
# _logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'


    repair_order_ids = fields.One2many(comodel_name="mrp.repair.order", string="Repair Order", required=False,
                                      default=False, inverse_name="partner_id")

    repair_order_count = fields.Integer(compute='_compute_repair_order', required=False, readonly=True)

    @api.multi
    def _compute_repair_order(self):
        for partner in self:
            partner.repair_order_count = len(partner.repair_order_ids) if partner.repair_order_ids else 0