# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    repair_order_id = fields.Many2one(comodel_name="mrp.repair.order", string="Repair order", required=False,
                                      default=False, ondelete='cascade', groups="mrp.group_mrp_user")