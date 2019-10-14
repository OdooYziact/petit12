# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo.tools.misc import split_every
from psycopg2 import OperationalError

from odoo import api, fields, models, registry, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round

from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

    


class ProcurementGroup(models.Model):
    """
    The procurement group class is used to group products together
    when computing procurements. (tasks, physical products, ...)

    The goal is that when you have one sales order of several products
    and the products are pulled from the same or several location(s), to keep
    having the moves grouped into pickings that represent the sales order.

    Used in: sales order (to group delivery order lines like the so), pull/push
    rules (to pack like the delivery order), on orderpoints (e.g. for wave picking
    all the similar products together).

    Grouping is made only if the source and the destination is the same.
    Suppose you have 4 lines on a picking from Output where 2 lines will need
    to come from Input (crossdock) and 2 lines coming from Stock -> Output As
    the four will have the same group ids from the SO, the move from input will
    have a stock.picking with 2 grouped lines and the move from stock will have
    2 grouped lines also.

    The name is usually the name of the original document (sales order) or a
    sequence computed if created manually.
    """
    _inherit = 'procurement.group'

    @api.model
    def run(self, product_id, product_qty, product_uom, location_id, name, origin, partner_id, values):
        values.setdefault('company_id', self.env['res.company']._company_default_get('procurement.group'))
        values.setdefault('priority', '1')
        values.setdefault('date_planned', fields.Datetime.now())
        rule = self._get_rule(product_id, location_id, values)

        if not rule:
            raise UserError(_('No procurement rule found. Please verify the configuration of your routes'))

        getattr(rule, '_run_%s' % rule.action)(product_id, product_qty, product_uom, location_id, name, origin, partner_id, values)
        return True

    @api.model
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False, partner_id=False):
        # Minimum stock rules
        self.sudo()._procure_orderpoint_confirm(use_new_cursor=use_new_cursor, company_id=company_id, partner_id=partner_id)
        # Search all confirmed stock_moves and try to assign them
        confirmed_moves = self.env['stock.move'].search([('state', '=', 'confirmed'), ('product_uom_qty', '!=', 0.0)], limit=None, order='priority desc, date_expected asc')
        for moves_chunk in split_every(100, confirmed_moves.ids):
            self.env['stock.move'].browse(moves_chunk)._action_assign()
            if use_new_cursor:
                self._cr.commit()

        exception_moves = self.env['stock.move'].search(self._get_exceptions_domain())
        for move in exception_moves:
            values = move._prepare_procurement_values()
            try:
                with self._cr.savepoint():
                    origin = (move.group_id and (move.group_id.name + ":") or "") + (move.rule_id and move.rule_id.name or move.origin or move.picking_id.name or "/")
                    self.run(move.product_id, move.product_uom_qty, move.product_uom, move.location_id, move.rule_id and move.rule_id.name or "/", origin, partner_id, values)
            except UserError as error:
                self.env['procurement.rule']._log_next_activity(move.product_id, error.name)
        if use_new_cursor:
            self._cr.commit()

        # Merge duplicated quants
        self.env['stock.quant']._merge_quants()

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id=False, partner_id=False):
        """ Call the scheduler in order to check the running procurements (super method), to check the minimum stock rules
        and the availability of moves. This function is intended to be run for all the companies at the same time, so
        we run functions as SUPERUSER to avoid intercompanies and access rights issues. """
        try:
            if use_new_cursor:
                cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=cr))  # TDE FIXME

            self._run_scheduler_tasks(use_new_cursor=use_new_cursor, company_id=company_id, partner_id=partner_id)
        finally:
            if use_new_cursor:
                try:
                    self._cr.close()
                except Exception:
                    pass
        return {}

    @api.model
    def _procure_orderpoint_confirm(self, use_new_cursor=False, company_id=False, partner_id=False):
        """ Create procurements based on orderpoints.
        :param bool use_new_cursor: if set, use a dedicated cursor and auto-commit after processing
            1000 orderpoints.
            This is appropriate for batch jobs only.
        """
        
        if company_id and self.env.user.company_id.id != company_id:
            # To ensure that the company_id is taken into account for
            # all the processes triggered by this method
            # i.e. If a PO is generated by the run of the procurements the
            # sequence to use is the one for the specified company not the
            # one of the user's company
            self = self.with_context(company_id=company_id, force_company=company_id)
        OrderPoint = self.env['stock.warehouse.orderpoint']
        domain = self._get_orderpoint_domain(company_id=company_id)
        orderpoints_noprefetch = OrderPoint.with_context(prefetch_fields=False).search(domain,
            order=self._procurement_from_orderpoint_get_order()).ids
        while orderpoints_noprefetch:
            if use_new_cursor:
                cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=cr))
            OrderPoint = self.env['stock.warehouse.orderpoint']

            orderpoints = OrderPoint.browse(orderpoints_noprefetch[:1000])
            orderpoints_noprefetch = orderpoints_noprefetch[1000:]

            # Calculate groups that can be executed together
            
            location_data = defaultdict(lambda: dict(products=self.env['product.product'], orderpoints=self.env['stock.warehouse.orderpoint'], groups=list()))
            for orderpoint in orderpoints:
                
                if partner_id :
                    list_partner=[]
                    for partner in orderpoint.product_id.seller_ids :
                        list_partner.append(partner.name)  
                if (partner_id and partner_id in list_partner) or not partner_id :      
                    key = self._procurement_from_orderpoint_get_grouping_key([orderpoint.id])
                    location_data[key]['products'] += orderpoint.product_id
                    location_data[key]['orderpoints'] += orderpoint
                    location_data[key]['groups'] = self._procurement_from_orderpoint_get_groups([orderpoint.id])

            for location_id, location_data in location_data.items():
                location_orderpoints = location_data['orderpoints']                
                product_context = dict(self._context, location=location_orderpoints[0].location_id.id)
                substract_quantity = location_orderpoints._quantity_in_progress()

                for group in location_data['groups']:
                    if group.get('from_date'):
                        product_context['from_date'] = group['from_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    if group['to_date']:
                        product_context['to_date'] = group['to_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    product_quantity = location_data['products'].with_context(product_context)._product_available()
                    for orderpoint in location_orderpoints:
                        try:
                            op_product_virtual = product_quantity[orderpoint.product_id.id]['virtual_available']
                            if op_product_virtual is None:
                                continue
                            if float_compare(op_product_virtual, orderpoint.product_min_qty, precision_rounding=orderpoint.product_uom.rounding) <= 0:
                                qty = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - op_product_virtual
                                remainder = orderpoint.qty_multiple > 0 and qty % orderpoint.qty_multiple or 0.0

                                if float_compare(remainder, 0.0, precision_rounding=orderpoint.product_uom.rounding) > 0:
                                    qty += orderpoint.qty_multiple - remainder

                                if float_compare(qty, 0.0, precision_rounding=orderpoint.product_uom.rounding) < 0:
                                    continue

                                qty -= substract_quantity[orderpoint.id]
                                qty_rounded = float_round(qty, precision_rounding=orderpoint.product_uom.rounding)
                                if qty_rounded > 0:
                                    values = orderpoint._prepare_procurement_values(qty_rounded, **group['procurement_values'])
                                    try:
                                        with self._cr.savepoint():
                                            self.env['procurement.group'].run(orderpoint.product_id, qty_rounded, orderpoint.product_uom, orderpoint.location_id,
                                                                              orderpoint.name, orderpoint.name, partner_id, values)
                                    except UserError as error:
                                        self.env['procurement.rule']._log_next_activity(orderpoint.product_id, error.name)
                                    self._procurement_from_orderpoint_post_process([orderpoint.id])
                                if use_new_cursor:
                                    cr.commit()

                        except OperationalError:
                            if use_new_cursor:
                                orderpoints_noprefetch += [orderpoint.id]
                                cr.rollback()
                                continue
                            else:
                                raise

            try:
                if use_new_cursor:
                    cr.commit()
            except OperationalError:
                if use_new_cursor:
                    cr.rollback()
                    continue
                else:
                    raise

            if use_new_cursor:
                cr.commit()
                cr.close()

        return {}
