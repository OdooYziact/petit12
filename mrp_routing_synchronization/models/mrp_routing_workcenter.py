# -*- coding: utf-8 -*-

# import logging
from odoo import api, fields, models, _
# _logger = logging.getLogger(__name__)


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    ### ADDING ###
    ref_id = fields.Integer(string='Ref.', readonly=True, default=-1)
    quality_point_ids = fields.One2many(comodel_name='quality.point', inverse_name='operation_id', copy=True)


    # ### OVERRIDE ###
    # @api.multi
    # def copy(self, default=None):
    #     self.ensure_one()
    #     default = dict(default or {}, ref_id=self.id)
    #     return super(MrpRouting, self).copy(default)


    @api.multi
    def _prepare_child_vals(self):
        """
        prepare current record values to update children
        :return: dict
        """

        self.ensure_one()
        return {
            'ref_id': self.id,
            'name': self.name,
            'workcenter_id': self.workcenter_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'expertise': self.expertise,
            'batch': self.batch,
            'batch_size': self.batch_size,
            'note': self.note,
            'worksheet': self.worksheet,
            'sequence': self.sequence,
        }