# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta




class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'partner.references.mixin']


    ### NEW ###
    partner_contact_id = fields.Many2one('res.partner', string='Contact', readonly=True, required=False,
                                         states={
                                             'draft': [('readonly', False)],
                                             'sent': [('readonly', False)]
                                         },
                                         help="Contact")

    fixed_cost_qty = fields.Float(string='Fixed cost quantity')
    fixed_cost_id = fields.Many2one(comodel_name='product.product', string='Fixed cost')
    fixed_cost_uom_id = fields.Many2one(related="fixed_cost_id.uom_id", readonly=True)
    fixed_cost_total = fields.Monetary(compute='_compute_fixed_cost_total', string='Total Fixed cost')
    is_waiting = fields.Boolean(string="Waiting for order reference", default=True)
    is_priority = fields.Boolean(compute='_compute_priority')
    total_purchase_price = fields.Float(string="Total Cost Price", compute="_compute_total_purchase_price")

    @api.multi
    @api.depends('order_line')
    def _compute_total_purchase_price(self):
        for record in self:
            # record.total_purchase_price = sum(record.order_line.mapped('purchase_price')) + record.fixed_cost_total
            record.total_purchase_price = sum([rec.purchase_price * rec.product_uom_qty for rec in record.order_line]) + record.fixed_cost_total

    @api.depends('requested_date', 'picking_ids')
    def _compute_priority(self):
        for record in self:
            record.is_priority = True if record.requested_date else False

    @api.depends('fixed_cost_id', 'fixed_cost_qty')
    def _compute_fixed_cost_total(self):
        for record in self:
            if record.fixed_cost_id:
                record.fixed_cost_total = record.fixed_cost_id.standard_price * record.fixed_cost_qty
            else:
                record.fixed_cost_total = 100.0

    def _compute_validity_date(self):
        if self.partner_id.sale_order_validity_date == '30days':
            self.validity_date = datetime.now() + timedelta(days=30)
        elif self.partner_id.sale_order_validity_date == '30days_eom':
            self.validity_date = datetime.now() + relativedelta(day=1, months=+2, days=-1)
        else:
            self.validity_date = ""

    @api.multi
    def button_print_picking(self):
        pickings = self.mapped('picking_ids').filtered(lambda rec: rec.state in ('done'))
        pickings.write({'printed': True})
        return self.env.ref('stock.action_report_delivery').report_action(pickings)

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()

        if self.partner_id.sale_order_validity_date:
            self._compute_validity_date()

    def _create_delivery_line(self, carrier, price_unit):
        SaleOrderLine = self.env['sale.order.line']
        if self.partner_id:
            # set delivery detail in the customer language
            carrier = carrier.with_context(lang=self.partner_id.lang)

        # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes, carrier.product_id, self.partner_id).ids

        # Create the sales order line
        values = {
            'order_id': self.id,
            'name': carrier.with_context(lang=self.partner_id.lang).name,
            'product_uom_qty': 1,
            'product_uom': carrier.product_id.uom_id.id,
            'product_id': carrier.product_id.id,
            'price_unit': 0.0,
            'purchase_price': price_unit,
            'tax_id': [(6, 0, taxes_ids)],
            'is_delivery': True,
        }
        if self.order_line:
            values['sequence'] = self.order_line[-1].sequence + 1
        sol = SaleOrderLine.sudo().create(values)
        return sol

    # @api.multi
    # def write(self, values):
    #     for so in self:
    #         if (('is_waiting' in values and values['is_waiting'] == False) or ('is_waiting' not in values and so.is_waiting == False)) \
    #                 and (('client_order_ref' in values and values['client_order_ref'] == False) or ('client_order_ref' not in values and self.is_waiting == False)):
    #             raise ValidationError(_('Please set reference order'))
    #
    #     return super(SaleOrder, self).write(values)


    @api.depends('order_line.margin', 'fixed_cost_total')
    def _product_margin(self):
        res = super(SaleOrder, self)._product_margin()

        for order in self:
            # TODO: utiliser les méthodes de calcul de coût des devis...
            order.margin -= order.fixed_cost_total


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        self.ensure_one()
        values.update({'is_priority': self.order_id.is_priority})

        return values

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        data = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        data.update({'is_priority': values.get('is_priority', False)})

        return data


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_priority = fields.Boolean(default=False)

    @api.model
    def create(self, vals):
        return super(StockMove, self).create(vals)


    def _get_new_picking_values(self):
        values = super(StockMove, self)._get_new_picking_values()
        values.update({'is_priority': self.is_priority})

        return values
