# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    ### OVERRIDDEN FIELDS ###
    # /!\ copy set to false
    operation_id = fields.Many2one('mrp.routing.workcenter', 'Step', copy=False, ondelete='cascade')
    routing_id = fields.Many2one(comodel_name='mrp.routing', copy=False)

    @api.onchange('product_id')
    def _onchange_product(self):
        """
        inherited onchange, add domain to routing_id field
        :return:
        """

        res = super(QualityPoint, self)._onchange_product()

        # product = self.product_id or self.product_tmpl_id.product_variant_ids[:1]
        bom_ids = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)])
        routing_ids = bom_ids.mapped('routing_id').ids
        # operation_ids = routing_ids.mapped('operation_ids').ids
        # routing_ids = res['domain']['operation_id'][0][2]

        res['domain']['routing_id'] = [('id', 'in', routing_ids)]
        self.operation_id = False

        # res['domain']['operation_id'] = [('id', 'in', operation_ids)]

        return res

    @api.onchange('routing_id')
    def _onchange_routing_id(self):

        routing_id = self.routing_id
        operation_ids = routing_id.operation_ids.ids

        return {
            'domain': {
                'operation_id': [('id', 'in', operation_ids)]
            }
        }