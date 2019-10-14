# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

# class StockMove(models.Model):
#     _inherit = 'stock.move'
#
#     repair_id = fields.Many2one('mrp.repair')

from random import shuffle, randint

class MrpRepairOrder(models.Model):
    _name = 'mrp.repair.order'
    _description = 'Repair Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'partner.references.mixin', 'document.attachment']
    _order = 'date_planned_finished desc, is_priority'

    ###### DEFAULT #####################################################################################################


    ###### FIELDS ######################################################################################################

    name = fields.Char(
        string="Deal number",
        default=lambda self: self.env['ir.sequence'].next_by_code('sale.order'),
        copy=False, required=True, readonly=True)

    # Product fields
    product_id = fields.Many2one(
        'product.product', string='Product',
        readonly=True, states={'draft': [('readonly', False)]})
    product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    product_qty = fields.Float(
        'Product Quantity',
        default=1.0, digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    product_uom = fields.Many2one(
        'product.uom', 'Product Unit of Measure',
        readonly=True, states={'draft': [('readonly', False)]})
    repair_model_id = fields.Many2one(comodel_name='mrp.repair.model', string='Repair model', readonly=True,
                                      states={'draft': [('readonly', False)]})
    product_category_id = fields.Many2one(comodel_name='product.category', string="Product category",
                                 related='repair_model_id.product_category_id', readonly=True)

    # Partner fields
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        required=True,
        readonly=True, index=True, states={'draft': [('readonly', False)]},
        help='Choose partner for whom the order will be invoiced and delivered.')
    partner_address_id = fields.Many2one(
        'res.partner', 'Delivery address',
        domain="[('parent_id','=',partner_id)]",
        readonly=True, states={'draft': [('readonly', False)]})
    default_address_id = fields.Many2one('res.partner', compute='_compute_default_address_id')
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice address')
    partner_contact_id = fields.Many2one('res.partner', string='Contact', readonly=True,
                                         states={'draft': [('readonly', False)]}, help="Contact")

    # State & Step
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('diagnostic', 'Diagnostic'),
        ('quotation', 'Quotation'),
        ('repair', 'Repair'),
        ('done', 'Done'),
        ('cancel', 'Canceled')],
        default='draft', string="Status",
        copy=False, readonly=True, required=True,
        help='The status of a repair line is set automatically to the one of the linked repair order.')
    step = fields.Selection(selection=[
        ('estimate', 'Estimate'),
        ('removal', 'Removal'),
        ('to_receive', 'To Receive'),
        ('to_disassemble', 'To Disassemble'),
        ('to_evaluate', 'To Evaluate'),
        ('to_consult', 'To Consult'),
        ('to_estimate', 'To Estimate'),
        ('to_restart', 'To Restart'),
        ('procurement', 'Procurement'),
        ('to_prepare', 'To Prepare'),
        ('under_repair', 'Under Repair'),
        ('done', 'Done'),
        ('to_deliver', 'To Deliver')],
        string="Step", copy=False, readonly=True)

    # Boolean fields
    waiting_for_approval = fields.Boolean(string="Waiting for customer approval", default=True, readonly=True,
                                          states={'draft': [('readonly', False)]})
    is_received = fields.Boolean(string="Received", compute='_compute_is_received', store=True)
    invoiced = fields.Boolean('Invoiced', compute='_compute_invoiced')
    repaired = fields.Boolean('Repaired', default=False, readonly=True)
    delivered = fields.Boolean('Delivered', default=False, readonly=True)
    is_confirmed = fields.Boolean('Confirmed', default=False, readonly=True)
    is_defined = fields.Boolean('Defined', default=False, readonly=True)
    is_consulted = fields.Boolean('Consulted', compute='_compute_is_consulted')
    is_expertised = fields.Boolean('Expertised', default=False, readonly=True)

    planned_method = fields.Selection(string="Repair time",
                                      selection=[('standard_time', 'Standard time'), ('fixed_date', 'Fixed date'), ],
                                      default='standard_time', readonly=False, required=True,
                                      states={'cancel': [('readonly', True)]})
    date_planned_finished = fields.Datetime(
        'Planned date', copy=False, default=fields.Datetime.now,
        index=True, readonly=False, required=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    is_priority = fields.Boolean(string="Priority", compute="_compute_priority", default=False, readonly=True)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot',
        readonly=True,
        domain="[('product_id','=', product_id)]",
        help="Products repaired are all belonging to this lot")


    # Invoice fields
    invoice_id = fields.Many2one(
        'account.invoice', 'Invoice',
        copy=False, readonly=True, track_visibility="onchange")
    invoice_count = fields.Integer(compute='_compute_invoice', string='# of Invoices')
    invoice_ids = fields.One2many(comodel_name='account.invoice', compute='_compute_invoice', string='Invoice')

    internal_notes = fields.Text('Internal Notes')
    quotation_notes = fields.Text('Quotation Notes')
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('mrp.repair'))

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', 'Ticket', readonly=False)

    stock_picking_ids = fields.One2many(comodel_name='stock.picking', inverse_name='repair_order_id', string='Stock picking')
    stock_picking_count = fields.Integer(compute='_compute_stock_picking', string='# Stock picking')

    receipt_date = fields.Datetime(string="Receipt date", compute='_compute_is_received')
    issue = fields.Text('Issue')
    recommendations = fields.Text('Comments', related='production_id.comments')

    # Specification fields
    specification_ids = fields.One2many(comodel_name='mrp.repair.data', inverse_name='repair_order_id',
                                        string='Specifications')
    specifications = fields.Char(string='Specifications', compute='_compute_specifications')

    # MO fields
    bom_id = fields.Many2one('mrp.bom', 'Nomenclature', domain="[('product_tmpl_id','=', product_tmpl_id)]",
                             readonly=True,
                             states={'draft': [('readonly', False)]})
    routing_id = fields.Many2one(comodel_name='mrp.routing', string='Routing', related='bom_id.routing_id',
                                 readonly=True)
    production_id = fields.Many2one(comodel_name='mrp.production', string='Production order')

    # Sale order fields
    sale_order_id = fields.Many2one('sale.order', '# Repair Order', readonly=True)
    sale_order_ids = fields.One2many(comodel_name='sale.order', inverse_name='repair_order_id', string='Quotation')

    # Cost fields
    total_cost = fields.Float(compute='_compute_cost', string='Total Cost')
    raw_material_cost = fields.Float(compute='_compute_cost', string='Raw Material Cost')
    operation_cost = fields.Float(compute='_compute_cost', string='Operations Cost')
    scrap_cost = fields.Float(compute='_compute_cost', string='Scrap Cost')
    currency_id = fields.Many2one(comodel_name='res.currency', default=lambda self: self.env.user.company_id.currency_id)
    operations_estimated_cost = fields.Float(compute='_compute_cost', string='Operations Estimated Cost')
    raw_material_estimated_cost = fields.Float(compute='_compute_cost', string='Raw Material Estimated Cost')
    total_estimated_cost = fields.Float(compute='_compute_cost', string='Estimated Cost')

    # Material request from MO
    request_ids = fields.One2many(related='production_id.request_ids')
    request_count = fields.Integer(related='production_id.request_count')
    request_line_ids = fields.One2many(related='production_id.request_line_ids')

    picking_type_in = fields.Many2one(comodel_name='stock.picking.type', string='Picking Type In',
                                      domain=[('code', 'in', ('outgoing', 'incoming'))])
    picking_type_out = fields.Many2one(comodel_name='stock.picking.type', string='Picking Type out')


    ###### COMPUTE #####################################################################################################

    @api.depends('request_line_ids', 'request_line_ids.state')
    @api.multi
    def _compute_is_consulted(self):
        for record in self:
            record.is_consulted = False if any([record.request_line_ids.filtered(lambda rec: rec.state not in ('done'))]) else True

    @api.depends('stock_picking_ids')
    @api.multi
    def _compute_stock_picking(self):
        for record in self:
            record.stock_picking_count = len(record.stock_picking_ids)

    @api.onchange('planned_method')
    def _compute_date_planned_finished(self):
        if self.planned_method == 'standard_time':
            standard_time = timedelta(weeks=3)
            self.date_planned_finished = datetime.now() + standard_time

    @api.multi
    @api.depends('planned_method')
    def _compute_priority(self):
        for repair in self:
            repair._is_priority = True if self.planned_method == 'fixed_date' else False

    @api.depends('sale_order_ids.invoice_ids')
    @api.multi
    def _compute_invoice(self):
        for record in self:
            record.invoice_ids = record.sale_order_ids.mapped('invoice_ids')
            record.invoice_count = sum(record.sale_order_ids.mapped('invoice_count'))

    @api.depends('invoice_ids')
    @api.multi
    def _compute_invoiced(self):
        for record in self:
            record.invoiced = True if len(record.invoice_ids) else False

    @api.depends('state', 'production_id')
    @api.multi
    def _compute_cost(self):

        for record in self:
            vals = {}
            if record.production_id and record.production_id.workorder_ids:

                workorder_ids = record.production_id.workorder_ids
                operation_cost = sum([sum(wo.time_ids.mapped('duration')) * wo.workcenter_id.costs_hour / 60 for wo in
                                      workorder_ids.filtered(lambda rec: rec.state in ('done')) if wo.time_ids])
                operations_estimated_cost = sum([wo.duration_expected * wo.workcenter_id.costs_hour / 60 for wo in
                                                 workorder_ids.filtered(lambda rec: rec.state not in ('cancel'))])
                scrap_cost = sum([sum(wo.time_ids.mapped('duration')) * wo.workcenter_id.costs_hour / 60 for wo in
                                      workorder_ids.filtered(lambda rec: rec.state in ('cancel')) if wo.time_ids])

                move_raw_ids = record.production_id.move_raw_ids
                raw_material_cost = sum([move.quantity_done * abs(move.price_unit) for move in
                                         move_raw_ids.filtered(lambda rec: rec.state in ('done'))])
                # raw_material_estimated_cost = sum([move.product_qty * move.product_id.standard_price for move in
                #                          move_raw_ids.filtered(lambda rec: rec.state not in ('cancel'))])

                request_line_ids = record.request_line_ids
                raw_material_estimated_cost = sum([line.product_qty * abs(line.price_unit) for line in
                     request_line_ids.filtered(lambda rec: rec.state in ('done'))])

                vals.update({
                    'operations_estimated_cost': operations_estimated_cost,
                    'raw_material_estimated_cost': raw_material_estimated_cost,
                    'total_estimated_cost': operations_estimated_cost + raw_material_estimated_cost,
                    'operation_cost': operation_cost,
                    'scrap_cost': scrap_cost,
                    'raw_material_cost': raw_material_cost,
                    'total_cost': operation_cost + raw_material_cost,
                })


            elif record.is_defined:
                operation_ids = record.bom_id.routing_id.operation_ids
                operations_estimated_cost = sum([op.time_cycle * op.workcenter_id.costs_hour / 60 for op in operation_ids])

                bom_line_ids = record.bom_id.bom_line_ids
                raw_material_estimated_cost = sum([line.product_qty * line.product_id.standard_price for line in bom_line_ids])

                vals.update({
                    'operations_estimated_cost': operations_estimated_cost,
                    'raw_material_estimated_cost': raw_material_estimated_cost,
                    'total_estimated_cost': operations_estimated_cost + raw_material_estimated_cost,
                    'operation_cost': 0.0,
                    # 'scrap_cost': 0.0,
                    'raw_material_cost': 0.0,
                    'total_cost': 0.0,
                })

            if vals:
                record.update(vals)


    @api.depends('specification_ids')
    def _compute_specifications(self):
        for order in self:
            specification_ids = order.specification_ids.search([('repair_order_id', '=', order.id)], limit=3)
            order.specifications = ", ".join([x[1] for x in specification_ids.name_get()]) if specification_ids else ""

    @api.one
    @api.depends('partner_id')
    def _compute_default_address_id(self):
        if self.partner_id:
            self.default_address_id = self.partner_id.address_get(['contact'])['contact']

    @api.depends('stock_picking_ids.state')
    @api.multi
    def _compute_is_received(self):
        # picking_type_id = 9

        for record in self:
            picking_ids = record.stock_picking_ids.filtered(lambda x: x.picking_type_id == record.picking_type_in and x.state in ('done'))
            if picking_ids:
                record.is_received = True
                record.receipt_date = picking_ids[0].scheduled_date
            else:
                record.is_received = False
                record.receipt_date = False

    ###### ACTIONS #####################################################################################################
    def action_view_delivery(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', self.stock_picking_ids.ids)]
        action['context'] = {
            'default_partner_id': self.partner_id.id,
            'default_move_lines': [(0, False, {'product_id': self.product_id.id})],
        }

        return action

    @api.multi
    def action_update_cost(self):
        return self._compute_cost()

    @api.multi
    def action_material_request_view(self):
        self.ensure_one()
        action = self.env.ref('mrp_repair_order.action_view_material_request_tree').read()[0]
        action['domain'] = ['&', ('res_id', '=', self.production_id.id), ('res_model', '=', 'mrp.production')]
        return action

    @api.multi
    def action_cancel(self):
        if self.filtered(lambda record: record.state == 'done'):
            raise UserError(_('Cannot cancel completed repairs.'))

        self.mapped('production_id').action_cancel()
        self.mapped('sale_order_ids').action_cancel()
        self.mapped('stock_picking_ids').filtered(lambda x: x.state not in ('done', 'cancel')).action_cancel()

        return self.write({'state': 'cancel'})

    @api.multi
    def action_close(self):
        """
        Force la fermeture d'une réparation
        TODO: traiter l'annulation
        :return: Boolean
        """
        # orders = self.filtered(lambda x: x.state in ('under_repair'))
        # orders.mapped('production_id').filtered(lambda x: x.state not in ('done', 'cancel')).action_end()
        # orders.update({'state': 'done'})

        orders = self.filtered(lambda x: x.state in ('under_repair', 'expertise', 'diagnostic', 'confirmed'))
        if orders.mapped('production_id').action_cancel():
            orders.write({'state': 'cancel'})

        return True

    @api.multi
    def action_invoice_create(self):
        if any(self.mapped('sale_order_id').filtered(lambda x: x.state not in ('repair_confirmed'))):
            raise ValidationError(_('Sale order should be confirmed in order to be invoiced'))

        return self.sale_order_id.action_invoice_create()

    @api.multi
    def action_confirm(self):
        self.write({'is_confirmed': True})

        records = self.filtered(lambda rec: rec.state == 'quotation' and rec.step == 'to_estimate')
        records.action_procurement()
        records.mapped('production_id').action_in_progress()
        records.mapped('production_id').mapped('workorder_ids').action_start()

        # self.filtered(lambda rec: rec.waiting_for_approval).write({'waiting_for_approval': False})
        # self.filtered(lambda rec: rec.state in ('quotation') and rec.step in ('to_estimate')).write({'state': 'repair','step': 'procurement'})
        return True

    @api.multi
    def action_procurement(self):
        self.filtered(lambda rec: rec.state in ('quotation') and rec.step in ('to_estimate')).write({'state': 'repair', 'step': 'procurement'})
        return self.request_ids.action_run()

    @api.multi
    def action_quotation(self):
        """
        Passe la réparation en status devis si le devis n'a pas encore été confirmé
        :return: Boolean
        """
        for order in self.filtered(lambda x: x.state == 'expertise'):
            vals = {'state': 'confirmed'} if order.sale_order_id.state == 'repair_confirmed' else {'state': 'quotation'}
            order.state.update(vals)

        return True

    @api.multi
    def action_repair_end(self):
        if any(self.filtered(lambda x: x.state not in ('repair') and x.production_id.state != 'done')):
            raise ValidationError(_("You can only finish repair order in progress."))

        self.write({'state': 'repair', 'step': 'done'})
        return True

    @api.multi
    def action_consult_done(self):
        records = self.filtered(lambda rec: rec.state in ('quotation') and rec.step in ('to_consult'))
        for record in records:
            if not record.is_confirmed or record.waiting_for_approval:
                record.write({'step': 'to_estimate'})
            else:
                record.write({'step': 'procurement', 'state': 'repair'})
        return True

    @api.multi
    def action_production_restart(self):
        records = self.filtered(lambda x: x.state in ('repair') and x.step in ('procurement'))
        records.mapped('production_id').action_in_progress()
        records.mapped('production_id').mapped('workorder_ids').action_start()

        return True

    @api.multi
    def action_expertise(self):
        return self.filtered(lambda x: x.state in ('diagnostic')).write({'step': 'to_evaluate'})

    @api.multi
    def action_expertise_done(self):
        self.write({'is_expertised': True})
        self.filtered(lambda x: x.state in ('diagnostic') and x.step in ('to_evaluate')).write({'state': 'quotation',
                                                                                                 'step': 'to_consult'})
        return self.mapped('production_id').action_waiting()

    @api.multi
    def action_diagnostic(self):
        self.ensure_one()

        if not self.sale_order_id:
            vals = self._prepare_sale_order()
            self.sale_order_id = self.env['sale.order'].create(vals)

        if any(self.filtered(lambda x: x.state not in ('draft'))):
            raise ValidationError(_('Repair order must be in draft state.'))

        self.specification_ids.check_required()

        for repair in self:
            vals = self._prepare_manufacture(repair)
            repair.production_id = self.env['mrp.production'].create(vals)

            if repair.product_id:
                repair.write({'state': 'diagnostic', 'step': 'to_disassemble'})
                repair.production_id.button_plan()
                repair.production_id.workorder_ids._update_state()
                # update workorders date_planned_finished with current value
                repair.production_id.workorder_ids.update({'date_planned_finished': repair.date_planned_finished})
            else:
                ValidationError(_('Error, diagnostic'))

        return True

    @api.multi
    def action_to_deliver(self):
        if any(self.filtered(lambda x: x.delivered or x.state not in ('done', 'invoiced', 'cancel'))):
            raise ValidationError(_('Repair must be done, invoiced or cancelled in order to delivery'))

        self.write({'state': 'to_deliver'})
        return True

    @api.multi
    def action_estimate(self):
        action = self.action_repair_quotation()
        self.write({'step': 'estimate'})

        return action

    @api.multi
    def action_view_sale_order(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': "Devis de réparation",
            'res_model': 'sale.order',
            'domain': [('repair_order_id', '=', self.id)],
            "views": [[False, "tree"], [False, "form"]],
            'context': {
                'search_default_is_open': True,
                'search_default_partner_id': self.partner_id.id,
                'default_repair_order_id': self.id,
            }
        }

        if self.partner_contact_id:
            action['context']['default_partner_contact_id'] = self.partner_contact_id.id

        action['context']['default_origin'] = self.sale_order_id.name if self.sale_order_id else self.name

        return action

    @api.multi
    def action_view_production(self):
        action = {
            "type": "ir.actions.act_window",
            "name": "Ordre de fabrication",
            "res_model": "mrp.production",
            "view_type": 'form',
            "views": [[False, "form"], [False, "tree"]],
            "target": 'current',
        }

        if self.production_id:
            action['res_id'] = self.production_id.id
        else:
            raise UserError(_(u"No linked repair."))

        return action

    @api.multi
    def action_view_workorder(self):
        tree_id = self.env.ref('mrp_repair_order.mrp_production_workorder_tree_view').id,
        action = {
            "type": "ir.actions.act_window",
            "name": "Ordres de travail",
            "res_model": "mrp.workorder",
            'view_id': self.env.ref('mrp_repair_order.mrp_production_workorder_tree_view').id,
            "views": [[tree_id, "tree"], [False, "form"]],
            'domain': [('production_id', '=', self.production_id.id)]
        }

        return action

    @api.multi
    def action_specifications(self):
        repair_data = self.env['mrp.repair.data']

        self._check_state_specs()

        for repair in self:
            #  create
            if not repair.specification_ids:
                specifications = repair_data.create_specifications(self._name, repair)
                specification_ids = [(6, False, specifications.ids)]
            #  update
            else:
                specifications = repair_data.get_specifications(repair)
                to_add = specifications.filtered(lambda x: x.id not in [s.specification_id.id for s in repair.specification_ids])
                specification_ids = [(4, repair_data.create({
                    'specification_id': x.id,
                    'repair_order_id': repair.id,
                    'required': x.required}).id, False) for x in to_add]

            repair.update({
                # 'state': 'specifications',
                'specification_ids': specification_ids,
            })

        return True

    @api.multi
    def action_product_confirm(self):
        if any(self.filtered(lambda rec: not rec.product_id or not rec.bom_id)):
            raise ValidationError('Please define repair product. ')
        self.write({'is_defined': True})
        return self.action_specifications()

    @api.multi
    def action_removal(self):
        """

        :return:
        """
        if any(self.filtered(lambda x: x.state not in ('draft'))):
            raise ValidationError(_('Only draft repair order can be received.'))

        if any(self.mapped('is_received')):
            raise ValidationError(_("Product can only be received once."))

        for record in self:
            vals = record._prepare_stock_picking_in()
            record.stock_picking_ids |= self.env['stock.picking'].create(vals)
            record.write({'step': 'removal'})

        return True

    @api.multi
    def action_receive_product(self):
        stock_picking = self.env['stock.picking']
        stock_move = self.env['stock.move']
        picking_type_id = self.env['stock.picking.type'].search([('name', '=', 'Réceptions')], limit=1)

        if any([state not in ('draft','estimate') for state in self.mapped('state')]):
            raise ValidationError(_('Only draft repair order can be received.'))

        if any([received for received in self.mapped('is_received')]):
            # FIXME: sans effet ! rollback à l'exception...
            self._force_received_state()
            raise ValidationError(_("Products can only be received once."))


        for record in self:
            vals = record._prepare_stock_picking_in()
            record.stock_picking_ids |= stock_picking.create(vals)
            record.write({'step': 'removal'})


        # for repair in self:
        #     # FIXME ou... self._default_stock_location()
        #     default_location_id = picking_type_id.default_location_dest_id.id
        #
        #     vals = self._prepare_stock_picking_in(repair, picking_type_id)
        #     stock_picking_id = stock_picking.create(vals)
        #
        #     # création d'un numéro de série (séquence auto)
        #     if not repair.lot_id:
        #         repair.lot_id = self._get_lot_id(repair.product_id)
        #
        #     move_vals = self._prepare_stock_move_in(repair, picking_type_id, stock_picking_id)
        #     stock_move_id = stock_move.create(move_vals)
        #     stock_move_id._action_assign()
        #     # stock_move_id._update_reserved_quantity(1.0, 0)
        #
        #     stock_picking_id.move_lines |= stock_move_id
        #     stock_picking_id.action_confirm()
        #     stock_picking_id.force_assign()
        #     stock_picking_id.action_done()
        #
        #     repair.stock_picking_id = stock_picking_id.id
        #     # repair.stock_picking_id.action_assign()
        #
        #     # réception OK, next state et update des emplacements
        #     if repair.stock_picking_id.state == 'done':
        #         repair.location_id = default_location_id
        #         repair.location_dest_id = default_location_id
        #
        #         repair.action_specifications()
        #
        #     # create sale order
        #     repair._create_sale_order()

        return True

    @api.multi
    def action_repair_quotation(self):
        self.ensure_one()

        if not self.sale_order_id:
            vals = self._prepare_sale_order()
            self.sale_order_id = self.env['sale.order'].create(vals)

        action = {
            'type': 'ir.actions.act_window',
            'name': "Devis de réparation",
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'domain': [('repair_order_id', '=', self.id)],
            "views": [[False, "form"], [False, "tree"]],
            'context': {
                'search_default_is_open': True,
                'search_default_partner_id': self.partner_id.id,
                'default_repair_order_id': self.id,
            }
        }

        if self.partner_contact_id:
            action['context']['default_partner_contact_id'] = self.partner_contact_id.id

        action['context']['default_origin'] = self.sale_order_id.name if self.sale_order_id else self.name

        return action

    ###### ONCHANGE ####################################################################################################

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.lot_id = False
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    @api.onchange('product_uom')
    def onchange_product_uom(self):
        res = {}
        if not self.product_id or not self.product_uom:
            return res
        if self.product_uom.category_id != self.product_id.uom_id.category_id:
            res['warning'] = {'title': _('Warning'), 'message': _('The Product Unit of Measure you chose has a different category than in the product form.')}
            self.product_uom = self.product_id.uom_id.id
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.partner_contact_id = False
        if not self.partner_id:
            self.partner_address_id = False
            self.partner_invoice_id = False
        else:
            addresses = self.partner_id.address_get(['delivery', 'invoice', 'contact'])
            self.partner_address_id = addresses['delivery'] or addresses['contact']
            self.partner_invoice_id = addresses['invoice']


    ###### BUSINESS ####################################################################################################

    def get_specifications(self):
        res = []

        for item in self.specification_ids:
            res.append("<strong>%s</strong> %s %s" % (item.description, item.value, item.unit)
                       if item.unit else "<strong>%s<strong> %s" % (item.description, item.value))

        return ", ".join(res)

    @api.model
    def _prepare_manufacture(self, repair_id):
        """
        Retourne un dictionnaire de valeurs pour la création d'une fabrication
        :param repair_id:
        :return: vals
        """
        vals = {
            'name': repair_id.name,
            'repair_order_id': repair_id.id,
            'product_id': repair_id.product_id.id,
            'product_qty': repair_id.product_qty,
            'product_uom_id': repair_id.product_uom.id,
            'bom_id': repair_id.bom_id.id,
            'routing_id': repair_id.routing_id.id,
            'origin': repair_id.name,
        }

        location = self.env.ref('mrp_repair_order.stock_location_manufacture', raise_if_not_found=False)
        if location:
            vals.update({'location_src_id': location.id})

        location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if location:
            vals.update({'location_dest_id': location.id})

        return vals

    def _prepare_sale_order(self):
        return {
            'name': self.name,
            'repair_order_id': self.id,
            'partner_id': self.partner_id.id,
            'partner_contact_id': self.partner_contact_id.id,
            'origin': self.name,
            'flag': 'repair',
            'user_id': self.partner_id.user_id.id,
            '_rel_id': self.id,
            '_rel_model': self._name,
        }

    def _create_sale_order(self):
        sale_order = self.env['sale.order']

        if not self.sale_order_id:
            vals = self._prepare_sale_order()
            self.sale_order_id = sale_order.create(vals)

    @api.multi
    def _check_state_specs(self):
        if any([record for record in self.filtered(lambda x: not x.repair_model_id or not x.product_id)]):
            raise UserError('Error !')

    def _get_lot_id(self, product_id):
        """
        Generate serial number (lot id) for product
        :param product_id:
        :return: recordset
        """
        return self.env['stock.production.lot'].create({
            'product_id': product_id.id,
        })

    def _prepare_stock_picking_in(self):
        move = self._prepare_stock_move_in()
        return {
            'repair_order_id': self.id,
            'location_id': self.picking_type_in.default_location_src_id.id or self.env.ref('stock.stock_location_customers').id,
            'location_dest_id': self.picking_type_in.default_location_dest_id.id,
            'picking_type_id': self.picking_type_in.id,
            'move_lines': [(0, False, move)],
            'partner_id': self.partner_id.id,
            'owner_id': self.partner_id.id,
            'origin': self.name,
        }

    def _prepare_stock_move_in(self):
        product_id = self.env.ref('mrp_repair_order.product_to_repair').product_variant_id

        if not self.lot_id:
            self.lot_id = self._get_lot_id(product_id)

        return{
            'name': product_id.name,
            'product_id': product_id.id,
            'product_uom': product_id.uom_id.id,
            'product_uom_qty': 1.0,
            'picking_id': self.picking_type_in.id,
            'ordered_qty': 1.0,
            # 'use_create_lots': True,
            'additional': True,
            'move_line_ids': [(0, 0, {
                'product_id': product_id.id,
                'location_id': self.picking_type_in.default_location_src_id.id or self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.picking_type_in.default_location_dest_id.id,
                'lot_id': self.lot_id.id,
                'lot_name': self.lot_id.name,
                'product_uom_qty': 1.0,
                'product_uom_id': product_id.uom_id.id,
                # 'qty_done': 1,
                'owner_id': self.partner_id.id,
            })]
        }

        # return{
        #     'name': repair_id.product_id.name,
        #     'product_id': repair_id.product_id.id,
        #     'product_uom': repair_id.product_uom.id,
        #     'product_uom_qty': repair_id.product_qty,
        #     'location_id': repair_id.location_id.id,
        #     'location_dest_id': picking_type_id.default_location_dest_id.id,
        #     'lot_id': repair_id.lot_id.id,
        #     'picking_id': stock_picking_id.id,
        #     'ordered_qty': 1.0,
        #     'use_create_lots': True,
        #     'additional': True,
        #     'move_line_ids': [(0, 0, {
        #         'product_id': repair_id.product_id.id,
        #         'lot_id': repair_id.lot_id.id,
        #         'lot_name': repair_id.lot_id.name,
        #         'product_uom_qty': repair_id.product_qty,
        #         'product_uom_id': repair_id.product_uom.id,
        #         'qty_done': 1,
        #         # 'package_id': False,
        #         # 'result_package_id': False,
        #         'owner_id': repair_id.partner_id.id,
        #         'location_id': repair_id.location_id.id,
        #         'location_dest_id': picking_type_id.default_location_dest_id.id, })],
        # }

    def _prepare_product_from_obj(self, obj):
        if not obj.product_id:
            return {}

        vals = {
            'product_id': obj.product_id,
            'description': "%s\n%s" % (obj.product_id.name_get()[0][1], obj.product_id.description_sale or ''),
            'product_uom_qty': obj.product_qty if hasattr(obj, 'product_qty') else obj.product_uom_qty,
        }

        if hasattr(obj, 'product_uom'):
            vals['product_uom'] = obj.product_uom


        return vals


    def _prepare_for_sale(self):
        # s'il y une fabrication: workorder + stock move
        if self.production_id:
            # move_raw = [{'product_id': x.product_id, 'product_uom_qty': x.product_uom_qty} for x in self.production_id.move_raw_ids]
            move_raw = [self._prepare_product_from_obj(rec) for rec in self.production_id.move_raw_ids]
            materials = self.production_id._prepare_material_request_for_sale()

            move_raw += list(filter(lambda item: item['product_id'] not in [rec['product_id'] for rec in move_raw], materials))

            vals = {'operations': self.production_id._prepare_for_sale(), 'materials': move_raw}
            _logger.critical(vals)
            return vals

        # sinon opérations + bom line
        else:
            # materials = [{'product_id': x.product_id, 'product_uom_qty': x.product_qty} for x in
            #              self.bom_id.bom_line_ids]
            materials = [self._prepare_product_from_obj(rec) for rec in self.bom_id.bom_line_ids]

            vals = {'operations': self.routing_id._prepare_for_sale(), 'materials': materials}
            _logger.critical(vals)
            return vals


    ###### ORM #########################################################################################################

    @api.multi
    def write(self, vals):
        # update workorders date_planned_finished from current record value
        for record in self:
            if 'date_planned_finished' in vals and vals.get('date_planned_finished') != record.date_planned_finished:
                if record.production_id and record.production_id.workorder_ids:
                    wo = record.production_id.workorder_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                    wo.write({'date_planned_finished': vals.get('date_planned_finished')})

        return super(MrpRepairOrder, self).write(vals)

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda x: x.state not in ('cancel'))):
            raise UserError(_("Repair must be canceled in order to remove it."))

        self.mapped('production_id').action_cancel()
        self.mapped('sale_order_ids').action_cancel()
        self.stock_picking_ids.action_cancel()
        self.stock_picking_ids.unlink()

        return super(MrpRepairOrder, self).unlink()


