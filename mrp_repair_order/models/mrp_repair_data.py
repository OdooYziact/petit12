# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
# import pudb
#
# import logging
# _logger = logging.getLogger(__name__)


class MrpRepairData(models.Model):
    _inherit = 'mrp.repair.data'

    repair_order_id = fields.Many2one(comodel_name="mrp.repair.order", string="Repair Order", required=True, ondelete='cascade')

    @api.model
    def _prepare_vals(self, field, model_name, model_id):
        res = super(MrpRepairData, self)._prepare_vals(field, model_name, model_id)

        if model_name == 'mrp.repair.order':
            res['repair_order_id'] = model_id.id

        return res