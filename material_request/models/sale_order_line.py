# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
# from odoo.exceptions import UserError, ValidationError

# import logging
# _logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    request_line_id = fields.Many2one(comodel_name="material.request.line")