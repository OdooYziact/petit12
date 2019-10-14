# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class QuyalityCheck(models.Model):
    _inherit = 'quality.check'

    ### INHERITS ###
    measure = fields.Float('Measure', default=None)

    ### ADDING ###
    attachment_id = fields.Many2one(comodel_name='ir.attachment', compute='_compute_attachment')


    @api.multi
    def _compute_attachment(self):
        env = self.env['ir.attachment']
        for record in self:
            if record.picture:
                record.attachment_id = env.search(['&', ('res_field', '=', 'picture'), ('res_id', '=', record.id),
                                                   ('res_model', '=', self._name)], limit=1)


    def _prepare_for_report(self):
        return {
            'title': self.title,
            'result': self.result,
            'summary': self.quality_state_for_summary,
            'state': self.quality_state,
            'test_type': self.test_type,
            'norm_unit': self.norm_unit,
            'measure': self.measure,
            'tolerance_min': self.tolerance_min,
            'tolerance_max': self.tolerance_max,
        }

