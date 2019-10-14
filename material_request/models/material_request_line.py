# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    request_id = fields.Many2one(comodel_name="material.request", string="Material request", readonly=True,
                                 ondelete="cascade")
    document_name = fields.Char(related='request_id.document_name', readonly=True, store=True)
    is_done = fields.Boolean(default=False)
    is_progress = fields.Boolean(default=False, compute='_compute_progress', store=True)
    active = fields.Boolean(default=True)
    name = fields.Char(string="name")
    description = fields.Text(string="Description")
    product_id = fields.Many2one(
        'product.product', string='Product',
        readonly=True, states={'draft': [('readonly', False)], 'new': [('readonly', False)]})
    product_qty = fields.Float(
        'Product quantity',
        default=1.0, digits=dp.get_precision('Product Unit of Measure'),
        readonly=False, required=True, states={'done': [('readonly', True)]})
    product_uom = fields.Many2one(
        'product.uom', "Unit of Measure",
        readonly=False, required=True, states={'done': [('readonly', True)]}, default=lambda self: self.env.ref('product.product_uom_unit').id)
    supplier_id = fields.Many2one(
        'res.partner', 'Supplier',
        readonly=True, index=True, states={'draft': [('readonly', False)]}, domain="[('supplier', '=', True)]",
        help='Supplier')
    request = fields.Selection(selection=[
        ('internal_picking', _('Internal picking')),
        ('request_for_creation', _('Request for creation'))],
        default='internal_picking', string="Request",
        copy=False, readonly=False, required=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('progress', 'Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('archived', 'Archived')],
        default='draft', copy=False, compute='_compute_state', store=True)
    purchase_line_id = fields.Many2one(comodel_name='purchase.order.line', ondelete="cascade")
    # price_unit = fields.Float(related='purchase_line_id.price_unit', readonly=True)
    price_unit = fields.Float(compute='_compute_price', store=True)
    price_total = fields.Float(compute='_compute_price')
    move_id = fields.Many2one(comodel_name='stock.move', readonly=True)
    rule_id = fields.Many2one(comodel_name='procurement.rule', compute='_compute_procurement_rule')
    action = fields.Selection(related='rule_id.action', readonly=True, required=False)
    procure_method = fields.Selection(related='rule_id.procure_method', readonly=True, required=False)
    purchase_order_count = fields.Integer(compute="_compute_purchase_order", string="# Purchase Order", store=True)
    purchase_order_ids = fields.One2many(comodel_name="purchase.order.line", inverse_name="request_line_id", string="Purchase order")
    currency_id = fields.Many2one(related='request_id.currency_id')

    @api.depends('purchase_line_id.price_unit', 'state', 'product_id', 'product_qty')
    @api.multi
    def _compute_price(self):
        for record in self:
            if not record.product_id:
                record.price_unit = 0.0
                record.price_total = 0.0
                continue

            if record.purchase_line_id:
                record.price_unit = record.purchase_line_id.price_unit
            else:
                record.price_unit = record.product_id.standard_price

            record.price_total = record.price_unit * record.product_qty

    @api.depends('is_done', 'is_progress')
    def _compute_state(self):
        for record in self:
            if record.is_done:
                record.state = 'done'
            elif not record.is_done and record.is_progress:
                record.state = 'progress'
            else:
                record.state = 'draft'

    @api.depends('purchase_order_count')
    def _compute_progress(self):
        for record in self:
            record.is_progress = True if record.purchase_order_count else False


    @api.depends('product_id', 'request', 'product_id.route_ids')
    @api.multi
    def _compute_procurement_rule(self):
        values = {'warehouse_id': self._default_warehouse_id()}
        location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

        for record in self:
            if record.product_id:
                record.rule_id = self.env['procurement.group']._get_rule(record.product_id, location, values)

    @api.depends('purchase_order_ids', 'request_id.purchase_order_count')
    @api.multi
    def _compute_purchase_order(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids.mapped('order_id')) or 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        vals = {}
        if self.product_id and self.product_id.uom_po_id:
            vals['value'] = self._prepare_product(self.product_id)

        return vals

    @api.model
    def _prepare_product(self, product_id):
        return {'name': product_id.name, 'product_uom': product_id.uom_po_id.id}

    @api.multi
    def action_done(self):
        return self.write({'is_done': True})

    @api.multi
    def action_cancel(self):
        if any([self.filtered(lambda x: x.is_done or x.state in ('done'))]):
            raise ValidationError(_('You can not cancel closed request lines.'))

        return True
