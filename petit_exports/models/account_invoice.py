# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    export_id = fields.Many2one(comodel_name='account.invoice.export')
    is_exported = fields.Boolean(compute='_compute_export', store=True)

    @api.depends('export_id')
    @api.multi
    def _compute_export(self):
        for record in self:
            record.is_exported = True if record.export_id else False

    @api.model
    def _export_invoice(self, start_date, end_date, journal):
        domain = [
            ('date_invoice', '>=', start_date),
            ('date_invoice', '<=', end_date),
            ('journal_id.type', '=', journal),
            ('state', 'in', ['open', 'paid'])
        ]
        if journal == 'purchase':
            domain.extend([('type', 'in', ['in_invoice', 'in_refund'])])
        elif journal == 'sale':
            domain.extend([('type', 'in', ['out_invoice', 'out_refund'])])
        return self.search(domain)