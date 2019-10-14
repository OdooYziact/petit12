# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price_related = fields.Float(related="standard_price", store=True)
