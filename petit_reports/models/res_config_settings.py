# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Texte a afficher sur toutes les factures
    invoicing_conditions = fields.Text(string='Termes et conditions')

    @api.model
    def get_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).get_values()

        res.update(
            invoicing_conditions=ICPSudo.get_param('invoicing_conditions'),
        )

        return res

    @api.multi
    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        super(ResConfigSettings, self).set_values()

        ICPSudo.set_param('invoicing_conditions', self.invoicing_conditions)