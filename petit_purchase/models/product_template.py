# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

class ProductTemplate(models.Model):
    _inherit = "product.template"

    supplier_code = fields.Char(compute='_compute_supplier_code', store=True, string="Référence fournisseur")

    @api.depends('seller_ids', 'seller_ids.product_code')
    @api.multi
    def _compute_supplier_code(self):
        for record in self:
            record.supplier_code = record.seller_ids.mapped('product_code')[0] if record.seller_ids.mapped('product_code') else ''