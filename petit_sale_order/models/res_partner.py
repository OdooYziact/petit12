# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = "res.partner"

    sale_order_validity_date = fields.Selection(string="Sale order validity date",
                             selection=[
                                 ('30days', '30 days'),
                                 ('30days_eom', '30 days ETM'),
                             ],
                             required=False,
                             default='30days')