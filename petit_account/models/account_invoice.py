# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountInvoice(models.Model):
    _name = 'account.invoice'

    origin_id = fields.Many2one(store=True)
