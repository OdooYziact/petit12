# -*- coding: utf-8 -*-

# import logging
from odoo import api, fields, models, _
# _logger = logging.getLogger(__name__)


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    ### ADDING ###
    ref_id = fields.Integer(string='Ref.', readonly=True, default=-1)

    @api.multi
    def _prepare_child_vals(self):
        """
        prepare current record values to update children
        :return: dict
        """

        self.ensure_one()
        return {
            'title': self.title,
            'product_tmpl_id': self.product_tmpl_id.id,
            'picking_type_id': self.picking_type_id.id,
            # 'routing_id': line.routing_id.id,
            # 'operation_id': line.operation_id.id,
            'measure_frequency_type': self.measure_frequency_type,
            'measure_frequency_value': self.measure_frequency_value,
            'test_type_id': self.test_type_id.id,
            'norm': self.norm,
            'norm_unit': self.norm_unit,
            'tolerance_min': self.tolerance_min,
            'tolerance_max': self.tolerance_max,
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
            'worksheet': self.worksheet,
            'worksheet_page': self.worksheet_page,
            'note': self.note,
            'reason': self.reason,
            'failure_message': self.failure_message,
            'sequence': self.sequence,
        }