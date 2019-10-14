# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountInvoiceExport(models.Model):
    _name = "account.invoice.export"

    invoice_ids = fields.One2many(comodel_name='account.invoice', inverse_name='export_id')
    invoice_count = fields.Integer(compute='_compute_invoice', store=True)
    journal = fields.Selection([('sale', 'Ventes'), ('purchase', 'Achats')], readonly=True)
    income = fields.Float(default=0.0, readonly=True)
    outcome = fields.Float(default=0.0, readonly=True)

    @api.depends('invoice_ids')
    @api.multi
    def _compute_invoice(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    ### ACTION ###
    def action_view_invoice(self):
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['domain'] = [('id', 'in', self.invoice_ids.ids)]
        return action

    @api.multi
    def name_get(self):
        return [(record.id, "%s %s" % (record.journal, fields.Datetime.from_string(record.create_date).strftime("%d/%m/%Y"))) for record in self]


    @api.multi
    def unlink(self):
        self.mapped('invoice_ids').write({'export_id': False})
        return super(AccountInvoiceExport, self).unlink()

