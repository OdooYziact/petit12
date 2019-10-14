# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import Counter
from datetime import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round

class PurchaseRequisitionLineWizard(models.TransientModel):
    _name = 'wizard.pr.line'


    wizard_id = fields.Many2one(comodel_name="wizard.pr", ondelete="cascade")
    material_request_line = fields.Many2one(comodel_name="material.request.line", ondelete="cascade")
    name = fields.Char(string="Name")
    description = fields.Text(string="Request description")
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float('Quantity', default=1.0, digits=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', "Unit of measure")
    supplier_id = fields.Many2one('res.partner', 'Supplier')


    @api.multi
    def name_get(self):
        return [(x.id, x.name) for x in self]


    def _prepare_vals(self, request_line):
        product_to_define = self.env.ref('material_request.product_to_define')

        return {
            'name': request_line.name if request_line.name else request_line.product_id.name,
            'description': request_line.description,
            'product_qty': request_line.product_qty,
            'product_uom': request_line.product_uom.id,
            'supplier_id': request_line.supplier_id.id,
            'product_id': request_line.product_id.id if request_line.product_id else product_to_define.id,
            'material_request_line': request_line.id,
        }


class PurchaseRequisitionWizard(models.TransientModel):
    _name = 'wizard.pr'
    _description = 'Create purchase requisition from material request'
    _rec_name = 'request_id'

    request_id = fields.Many2one('material.request', 'Material request', required=True, readonly=True,
                                 ondelete="cascade")
    request_line = fields.One2many(comodel_name='wizard.pr.line', readonly=False, inverse_name="wizard_id")


    @api.model
    def default_get(self, fields):
        res = super(PurchaseRequisitionWizard, self).default_get(fields)

        if 'request_id' in fields and not res.get('request_id') and self._context.get('active_model') == 'material.request' and self._context.get('active_id'):
            res['request_id'] = self._context['active_id']

        request_id = self.env['material.request'].browse(res['request_id'])
        wizard_line = self.env['wizard.pr.line']

        if request_id:
            res['request_line'] = [(0, False, wizard_line._prepare_vals(line)) for line in request_id.request_line.filtered(lambda x: x.state not in ('cancelled', 'archived'))]

        return res


    @api.multi
    def action_create_purchase_requisition(self):

        for wizard in self:
            lines = wizard._prepare_requisition_lines()

            return {
                'type': 'ir.actions.act_window',
                'name': _('Create purchase requisition'),
                'res_model': 'purchase.requisition',
                'view_mode': 'form',
                'context': {
                    'default_request_id': wizard.request_id.id,
                    'default_line_ids': lines,
                    'default_origin': wizard.request_id.name,
                }
            }


    def _prepare_requisition_lines(self):
        lines = []

        for line in self.request_line:
            lines.append({
                'name': line.name,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'qty_ordered': line.product_qty,
                'product_qty': line.product_qty,
                'request_line_id': line.material_request_line.id,
            })

        return lines
