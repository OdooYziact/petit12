# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    capital = fields.Float(string="Capital")