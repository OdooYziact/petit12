# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
#
# import logging
# _logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'custom.popup.mixin']


    show_details = fields.Boolean(string="Show detailed lines", default=False, readonly=True,
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    print_details = fields.Boolean(string="Show detailed lines on report", default=True)
    repair_order_id = fields.Many2one(comodel_name="mrp.repair.order", string="Repair order", required=False,
                                      default=False, ondelete='cascade', groups="mrp.group_mrp_user")
    total_estimated_cost = fields.Float(related='repair_order_id.total_estimated_cost', string='Total Estimated Cost',
                                        groups="mrp.group_mrp_user")
    raw_material_estimated_cost = fields.Float(related='repair_order_id.raw_material_estimated_cost',
                                               string='Raw Material Estimated Cost', groups="mrp.group_mrp_user")
    operations_estimated_cost = fields.Float(related='repair_order_id.operations_estimated_cost',
                                             string='Operations Estimated Cost', groups="mrp.group_mrp_user")
    shipping_cost = fields.Float(compute='_compute_shipping_cost', string='Shipping Cost')

    flag = fields.Selection(string="Type",
                             selection=[
                                 ('repair', 'REPARATION'),
                                 ('quotation', 'NEGOCE'),
                             ],
                             required=False,
                            default='quotation')

    state = fields.Selection(selection_add=[('repair_confirmed', 'Repair confirmed')])
    ready_to_sync = fields.Boolean(compute='_compute_ready_to_sync')
    warning = fields.Char(compute='_compute_warning')
    request_line_ids = fields.One2many(related='repair_order_id.request_line_ids')



    @api.depends('order_line', 'order_line.product_id')
    @api.multi
    def _compute_shipping_cost(self):
        categ_id = self.env.ref('__export__.product_category_689') or \
                   self.env['product.category'].search([('name', 'ilike', 'transport')], limit=1)[0]
        for record in self:
            record.shipping_cost = sum(record.order_line.filtered(lambda rec: rec._compare_category(categ_id)).mapped('purchase_price')) or 0.0

    @api.depends('repair_order_id.state', 'repair_order_id.step')
    @api.multi
    def _compute_warning(self):
        for record in self:
            if record.repair_order_id:
                repair_id = record.repair_order_id
                if repair_id.waiting_for_approval and repair_id.state not in ('quotation'):
                    record.warning = 'expertise not...'
                else:
                    record.warning = False
            else:
                record.warning = False

    @api.multi
    def _compute_ready_to_sync(self):
        for record in self:
            record.ready_to_sync = True if record.flag == 'repair' and record.state in ('draft', 'sent') else False

    @api.multi
    def action_quotation_send(self):
        action = super(SaleOrder, self).action_quotation_send()
        force_mail = self._context.get('force_mail', False)

        if self.repair_order_id and not force_mail:
            repair_id = self.repair_order_id
            if repair_id.waiting_for_approval and repair_id.state not in ('quotation', 'order'):

                context = {
                    'default_message': _('Expertise not done, are you sure to continue ?'),
                    'default_action': 'action_quotation_send',
                    'force_mail': True,
                }
                action = self._action_popup('Send by Email', context)

            elif not repair_id.waiting_for_approval and repair_id.state in ('order') and repair_id.step not in ('done'):

                context = {
                    'default_message': _("All operations aren't done, are you sure to continue ?"),
                    'default_action': 'action_quotation_send',
                    'force_mail': True,
                }
                action = self._action_popup('Send by Email', context)

        return action

    @api.multi
    def action_view_repair_order(self):
        """
        lien vers la réparation
        :return: ir.actions.act_window
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Réparation',
            'res_model': 'mrp.repair.order',
            "view_type": 'form',
            "views": [[False, "form"], [False, "tree"]],
            'res_id': self.repair_order_id.id,
            "target": 'current',
        }

    # Pour obtenir les lignes lorsque show_details = False, pour faire un récap avant les détails
    def get_lines_not_detailed_for_report(self):
        if self.show_details == True and self.flag == 'repair':
            return [{
                'product_uom': self.repair_order_id.product_id.uom_id.name,
                'name': self.repair_order_id.product_id.name,
                'product_uom_qty': 1,
            }]

    @api.onchange('show_details')
    def _onchange_show_details(self, from_report=False):
        """
        :param from_report: si on vient d'un report, on retourne les données à inscrire sur celui-ci, sinon on effectue le changement lié à show_details
        :return:
        """
        if self.flag == 'repair':
            vals = self._repair_sync()

            ids = []
            for line in vals:
                res = self.order_line.new(line)

                ids.append(res.id)


            return {'value': {'order_line': [(6, False, ids)]}}

        return {}

    @api.multi
    def action_repair_confirm(self):
        # self._action_repair_confirm()
        self.write({
            'state': 'sent',
            'confirmation_date': fields.Datetime.now()
        })
        self.mapped('repair_order_id').action_confirm()
        # self.action_confirm()
        return True

    @api.multi
    def _action_repair_confirm(self):

        request_ids = self.order_line.mapped('request_line_id.request_id')
        if request_ids:
            request_ids.action_run()

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'repair_confirmed',
            'confirmation_date': fields.Datetime.now()
        })
        if self.env.context.get('send_email'):
            self.force_quotation_send()

        # create an analytic account if at least an expense product
        if any([expense_policy != 'no' for expense_policy in self.order_line.mapped('product_id.expense_policy')]):
            if not self.analytic_account_id:
                self._create_analytic_account()

        return True

    def _get_tax_id(self, product_id):
        fpos = self.fiscal_position_id or self.partner_id.property_account_position_id
        # If company_id is set, always filter taxes by the company
        taxes = product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
        return fpos.map_tax(taxes, product_id, self.partner_shipping_id) if fpos else taxes

    def _get_purchase_price(self, pricelist, product, product_uom, date):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = pricelist.currency_id
        purchase_price = product.standard_price
        if product_uom != product.uom_id:
            purchase_price = product.uom_id._compute_price(purchase_price, product_uom)
        ctx = self.env.context.copy()
        ctx['date'] = date
        return frm_cur.with_context(ctx).compute(purchase_price, to_cur, round=False)

    def _get_price_unit(self, product_id, product_uom_qty):
        product_context = dict(self.env.context, partner_id=self.partner_id.id,
                               date=self.date_order, uom=product_id.uom_id.id)

        price_unit, rule_id = self.pricelist_id.with_context(product_context).get_product_price_rule(
            product_id, product_uom_qty, self.partner_id)

        return price_unit

    def _prepare_order_line(self, vals):
        product_id = vals.get('product_id', False)
        default_product_id = self.env.ref('mrp_repair_order.generic_repair_product_operation',
                                          raise_if_not_found=False).product_variant_id or False

        is_operation = True if vals.get('operation_id', False) or vals.get('product_id') == default_product_id else False

        if not product_id:
            return False

        # layout_category_id
        layout_cat_1 = self.env.ref('sale.sale_layout_cat_1')
        layout_cat_2 = self.env.ref('sale.sale_layout_cat_2')

        # force quantity to 1
        product_uom_qty = 1.0
        # product_uom_qty = vals.get('product_uom_qty', 0)
        price_unit = self._get_price_unit(product_id, product_uom_qty)
        tax_id = self._get_tax_id(product_id)


        if is_operation:
            purchase_price = (vals.get('product_uom_qty', 1.0) / 60) * vals.get('cost_hour')
            category_id = layout_cat_1
        else:
            purchase_price = self._get_purchase_price(self.pricelist_id, product_id, product_id.uom_id, self.date_order)
            category_id = layout_cat_2


        name = product_id.name_get()[0][1]

        if vals.get('name', False) and not product_id.description_sale:
            name = vals.get('name', 'Operation')
            if vals.get('note', False):
                name += '\n' + vals.get('note')
        elif product_id.description_sale:
            name += '\n' + product_id.description_sale or ''

        order_line = {
            'order_id': self.id,
            'name': name,
            'product_id': product_id.id,
            'price_unit': price_unit,
            'tax_id': [(6, False, tax_id.ids)],
            'purchase_price': purchase_price,
            'product_uom': product_id.uom_id.id,
            'product_uom_qty': product_uom_qty,
            'layout_category_id': category_id.id,
        }

        if vals.get('request_line_id'):
            order_line.update({
                'request_line_id': vals.get('request_line_id'),
            })

        operation_id = vals.get('operation_id', False)
        if operation_id:
            order_line.update({
                'operation_id': operation_id.id,
            })


        return order_line

    def _repair_sync(self):
        """

        :return: [{order_line}]
        """

        repair_id = self.repair_order_id
        order_lines = []
        amount_untaxed = 0.0
        purchase_price = 0.0

        data = repair_id._prepare_for_sale()

        for vals in data['operations'] + data['materials']:
            order_line = self._prepare_order_line(vals)
            if not order_line or not order_line.get('product_id', False):
                # FIXME: do nothing...
                continue

            purchase_price += order_line['purchase_price'] * order_line['product_uom_qty']
            amount_untaxed += order_line['price_unit'] * order_line['product_uom_qty']


            order_lines.append(order_line)

        if not self.show_details:

            tax_id = self._get_tax_id(repair_id.product_id)
            purchase_price = self.total_estimated_cost

            # layout_cat_2 = self.env.ref('sale.sale_layout_cat_2')
            # materials = [item for item in order_lines if item['layout_category_id'] == layout_cat_2.id]

            description = "%s\n%s" % (repair_id.product_id.name_get()[0][1], repair_id.product_id.description_sale) \
                if not self.print_details else repair_id.product_id.name

            order_lines = [{
                'order_id': self.id,
                'product_id': repair_id.product_id.id,
                'product_uom': repair_id.product_id.uom_id.id,
                'name': description,
                'product_uom_qty': 1,
                # 'price_unit': amount_untaxed,
                'purchase_price': purchase_price,
                'tax_id': [(6, False, tax_id.ids)],
                'layout_category_id': self.env.ref('sale.sale_layout_cat_1').id,
            }]

        return order_lines

    # @api.depends('show_details')
    @api.multi
    def action_repair_sync(self):

        for order in self:
            vals = order._repair_sync()

            order.sudo().write({'order_line': [(5, False, False)] + [(0, False, values) for values in vals]})
            # order.update({'order_line': vals})

        return True

    @api.depends('state', 'order_line.invoice_status')
    def _get_invoiced(self):
        super(SaleOrder, self)._get_invoiced()

        for order in self:
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
            # 'account.invoice.refund')
            # use like as origin may contains multiple references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search([('origin', 'like', order.name), ('company_id', '=', order.company_id.id)]).filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
            # Search for refunds as well
            refund_ids = self.env['account.invoice'].browse()
            if invoice_ids:
                for inv in invoice_ids:
                    refund_ids += refund_ids.search([('type', '=', 'out_refund'), ('origin', '=', inv.number), ('origin', '!=', False), ('journal_id', '=', inv.journal_id.id)])

            # Ignore the status of the deposit product
            deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
            line_invoice_status = [line.invoice_status for line in order.order_line if line.product_id != deposit_product_id]

            if order.state == 'repair_confirmed' and any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'

                order.update({
                    'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                    'invoice_ids': invoice_ids.ids + refund_ids.ids,
                    'invoice_status': invoice_status
                })

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({'repair_order_id': self.repair_order_id.id})

        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_category_id(self):
        return self.product_id.categ_id

    def _compare_category(self, category_id):
        return True if self._get_category_id() == category_id else False