import logging
from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    practice_ids = fields.Many2many(comodel_name="partner.practices", string="Practices")
    reference_ids = fields.Many2many(comodel_name="partner.references", string="References")

    has_references = fields.Boolean(string="références", compute="_compute_has_references")
    has_practices = fields.Boolean(string="habitudes", compute="_compute_has_references")


    @api.multi
    def _compute_has_references(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()

        has_references = ICPSudo.get_param('partner_references_fields')
        has_practices = ICPSudo.get_param('partner_practices_fields')

        for partner in self:
            partner.update({
                'has_references': bool(has_references),
                'has_practices': bool(has_practices),
            })



