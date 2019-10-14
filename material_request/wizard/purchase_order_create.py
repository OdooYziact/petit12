# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import Counter
from datetime import datetime

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round

class PurchaseOrderLineCreate(models.TransientModel):
    _name = 'purchase.order.line.create'


    wizard_id = fields.Many2one(comodel_name="purchase.order.create", ondelete="cascade")
    material_request_line = fields.Many2one(comodel_name="material.request.line")
    name = fields.Char(string="Name")
    description = fields.Text(string="request description")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float('Quantity', default=1.0, digits=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom = fields.Many2one('product.uom', "Unit of Measure", required=True)


    @api.multi
    def name_get(self):
        return [(x.id, x.name) for x in self]


    def _prepare_vals(self, request_line):
        product_to_define = self.env.ref('material_request.product_to_define')

        return {
            'name': "[%s]\n%s" % (request_line.name, request_line.description) if request_line.description else request_line.name,
            'description': request_line.description,
            'product_qty': request_line.product_qty,
            'product_uom': request_line.product_uom.id,
            'product_id': request_line.product_id.id if request_line.product_id else product_to_define.id,
            'material_request_line': request_line.id,
        }

    @api.multi
    def _prepare_order_line(self):
        lines = []

        for line in self:
            date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            lines.append({
                'name': line.name if line.name else line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'qty_ordered': line.product_qty,
                'product_qty': line.product_qty,
                'request_line_id': line.material_request_line.id,
                'date_planned': date_planned,
            })

        return lines

class PurchaseOrderCreate(models.TransientModel):
    _name = 'purchase.order.create'
    _description = 'Create purchase order from material request'
    _rec_name = 'request_id'

    request_id = fields.Many2one('material.request', 'Material request', required=True, readonly=True,
                                 ondelete="cascade")
    wizard_line = fields.One2many(comodel_name='purchase.order.line.create', readonly=False, inverse_name="wizard_id",
                                  ondelete="cascade")
    partner_id = fields.Many2one(comodel_name='res.partner', required=True, string="Supplier",
                                 domain=[('supplier', '=', True)])


    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrderCreate, self).default_get(fields)

        if 'request_id' in fields and not res.get('request_id') and self._context.get('active_model') == 'material.request' and self._context.get('active_id'):
            res['request_id'] = self._context['active_id']

        request_id = self.env['material.request'].browse(res['request_id'])
        wizard_line = self.env['purchase.order.line.create']

        if request_id:
            res['wizard_line'] = [(0, False, wizard_line._prepare_vals(line)) for line in
                                  request_id.request_line.filtered(lambda x: x.state in ('draft', 'progress'))]

        return res


    @api.multi
    def action_create_purchase_order(self):
        for wizard in self:
            lines = wizard.wizard_line._prepare_order_line()
            if not len(lines):
                return False

            return {
                'type': 'ir.actions.act_window',
                'name': _('Create purchase order'),
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'context': {
                    'default_request_id': wizard.request_id.id,
                    'default_partner_id': wizard.partner_id.id,
                    'default_order_line': lines,
                    'default_origin': wizard.request_id.document_name,
                    'default_date_planned': lines[0]['date_planned'],
                }
            }

