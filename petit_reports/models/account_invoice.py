# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Texte a afficher sur toutes les factures
    invoicing_conditions = fields.Text(string="Termes et conditions", compute="_compute_invoicing_conditions")
    origin_id = fields.Many2one(comodel_name='sale.order', compute="_compute_origin_id", store=True)

    @api.multi
    def _compute_invoicing_conditions(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()

        invoicing_conditions = ICPSudo.get_param('invoicing_conditions')

        for invoice in self:
            invoice.update({
                'invoicing_conditions': invoicing_conditions,
            })

    @api.multi
    def _compute_origin_id(self):
        for record in self:
            record.origin_id = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)