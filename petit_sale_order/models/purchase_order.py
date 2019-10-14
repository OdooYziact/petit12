# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    partner_contact_id = fields.Many2one('res.partner', string='Contact')