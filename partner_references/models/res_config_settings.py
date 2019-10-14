import logging
# from ast import literal_eval
from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    partner_references_fields = fields.Boolean(string='Références', default=False)
    partner_practices_fields = fields.Boolean(string='Habitudes', default=False)


    @api.model
    def get_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).get_values()

        res.update(
            partner_references_fields=ICPSudo.get_param('partner_references_fields'),
            partner_practices_fields=ICPSudo.get_param('partner_practices_fields'),
        )

        return res


    @api.multi
    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).set_values()

        ICPSudo.set_param('partner_references_fields', self.partner_references_fields)
        ICPSudo.set_param('partner_practices_fields', self.partner_practices_fields)

        return res

