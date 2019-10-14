# -*- coding: utf-8 -*-


from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class MaterialRequest(models.Model):
    _name = 'material.request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "name asc"


    name = fields.Char(string="request reference", default='/', copy=False, required=True, readonly=True,
                       states={'draft': [('readonly', True)]})
    active = fields.Boolean(default=True)
    is_approved = fields.Boolean(string="Approved", default=False, required=True)
    is_done = fields.Boolean(string="Done", default=False, required=True)
    is_progress = fields.Boolean(string="In Progress", compute='_compute_progress', store=True)
    note = fields.Text('Note')
    employee = fields.Many2one('res.users', string='Employee', default=lambda self: self.env.user,
                              track_visibility="onchange", readonly=True, states={'draft': [('readonly', False)]})
    responsible = fields.Many2one('res.users', string='Responsible', track_visibility="onchange",
                                  readonly=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    request_date = fields.Datetime(
        'Request date', copy=False, default=fields.Datetime.now,
        index=True, readonly=True, required=True)

    request_deadline = fields.Datetime(
        'Deadline', copy=False, default=fields.Datetime.now,
        index=True, required=True, readonly=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    res_id = fields.Integer(default=0, required=True)
    res_model = fields.Char(required=True)
    model_name = fields.Char(string="Origin document", compute="_compute_model_name", store=True)
    document_name = fields.Char(string="Reference origin", compute="_compute_model_name", store=True)

    purchase_requisition_ids = fields.One2many(comodel_name="purchase.requisition", inverse_name="request_id", string="Purchase requisition")
    purchase_requisition_count = fields.Integer(compute="_compute_purchase_count", string="# Purchase requisition", store=True)
    # purchase_order_ids = fields.One2many(comodel_name="purchase.order", compute="_compute_purchase_order", string="Purchase order")
    purchase_order_count = fields.Integer(compute="_compute_purchase_count", string="# Purchase order", store=True)
    purchase_order_ids = fields.One2many(comodel_name="purchase.order", inverse_name="request_id", string="Purchase order")
    currency_id = fields.Many2one(comodel_name='res.currency',
                                  default=lambda self: self.env.user.company_id.currency_id)

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('progress', 'In progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')],
        default='draft', required=True,
        compute='_compute_state', store=True)

    request_line = fields.One2many(string="Request lines", comodel_name="material.request.line", inverse_name="request_id",
                                   ondelete='cascade', track_visibility="onchange", readonly=False,
                                   states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    request_line_done = fields.One2many(string="Request lines", comodel_name="material.request.line", inverse_name="request_id",
                                   readonly=True, domain=[('active', '=', False)])


    @api.depends('is_approved', 'is_done', 'is_progress', 'request_line.state')
    def _compute_state(self):
        for record in self:
            if not record.is_approved and not record.is_progress and not record.is_done:
                record.state = 'draft'
            elif record.is_done:
                record.state = 'done'
            elif not record.is_done and (record.is_progress or record.is_approved) \
                    and not any(record.request_line.filtered(lambda rec: rec.state not in ('done', 'cancel'))):
                record.state = 'done'
                # record.action_confirm()

            elif not record.is_done and (record.is_progress or record.is_approved):
                record.state = 'progress'
            else:
                record.state = 'draft'

    @api.depends('purchase_requisition_count', 'purchase_order_count')
    def _compute_progress(self):
        for record in self:
            record.is_progress = True if (record.purchase_requisition_count or record.purchase_order_count) else False

    @api.depends('purchase_order_ids', 'purchase_requisition_ids')
    def _compute_purchase_count(self):
        for record in self:
            vals = {}
            vals['purchase_order_count'] = len(record.purchase_order_ids.filtered(lambda rec: rec.state not in ('cancel')))
            vals['purchase_requisition_count'] = len(record.purchase_requisition_ids.filtered(lambda rec: rec.state not in ('cancel')))

            record.update(vals)

    @api.multi
    @api.depends('res_model')
    def _compute_model_name(self):
        for requisition in self:
            if requisition.res_model and requisition.res_id:
                model = self.env['ir.model'].search([('model', '=', requisition.res_model)])
                if len(model):
                    requisition.model_name = model[0].name

                document = self.env[str(requisition.res_model)].browse(requisition.res_id)
                if len(document):
                    requisition.document_name = document.name

    @api.multi
    @api.depends('res_model')
    def _compute_document(self):
        for requisition in self:
            if requisition.res_model and requisition.res_id:
                document = self.env[str(requisition.res_model)].browse(requisition.res_id)
                if len(document):
                    requisition.document_name = document.name

    @api.multi
    def action_view_document(self):
        action = {
            "type": "ir.actions.act_window",
            "name": self.model_name,
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_type": 'form',
            "views": [[False, "form"], [False, "tree"]],
            "target": 'current',
        }

        return action

    @api.multi
    def action_approve(self):
        if any(self.filtered(lambda x: x.state not in ('draft'))):
            raise ValidationError(_('Request must be in draft to be approved.'))

        self.action_assign_to_me()

        return self.write({'is_approved': True})


    @api.multi
    def action_confirm(self):
        if any([self.mapped('request_line').filtered(lambda x: not x.product_id)]):
            raise ValidationError(_('Please remove or replace temporary lines'))

        self.request_line.filtered(lambda x: not x.is_done).write({'is_done': True})
        self.purchase_order_ids.filtered(lambda rec: rec.state != 'retained').button_cancel()

        return self.write({'is_done': True})


    @api.multi
    def action_cancel(self):
        if any([self.filtered(lambda x: x.state in ('done'))]):
            raise ValidationError(_('You can not cancel finished requests.'))

        self.mapped('request_line').action_cancel()
        self.mapped('purchase_order_ids').button_cancel()
        self.mapped('purchase_requisition_ids').action_cancel()

        return self.write({'active': False})


    @api.multi
    def action_run(self):

        stock_location_production = self.env.ref('stock.location_production')
        stock = self.env.ref('stock.stock_location_stock')
        stock_manufacture = self.env.ref('mrp_repair_order.stock_location_manufacture')
        picking_type_manufacture = self.env.ref('mrp_repair_order.picking_type_manufacture')


        # group_id.write({
        #     'sale_id': line.order_id.id,
        #     'partner_id': line.order_id.partner_shipping_id.id,
        # })

        for record in self.filtered(lambda rec: rec.state in ('done')):

            if not record.res_model or not record.res_id:
                continue

            doc = self.env[str(record.res_model)].browse(record.res_id)
            group_id = doc.procurement_group_id if hasattr(doc, 'procurement_group_id') else False
            picking_id = self.env['stock.picking'].search([('group_id', '=', group_id.id)], limit=1) or False

            request_line_ids = record.mapped('request_line').filtered(lambda rec: rec.state in ('done'))
            order_line_ids = request_line_ids.mapped('purchase_line_id').filtered(lambda rec: rec.order_id.state in ('retained'))
            order_ids = order_line_ids.mapped('order_id')

            if not picking_id:
                picking_id = self.env['stock.picking'].create({
                    'location_id': stock.id,
                    'location_dest_id': stock_manufacture.id,
                    'origin': doc.name,
                    'picking_type_id': picking_type_manufacture.id,
                    'group_id': group_id.id,
                })

            order_ids.write({'origin': doc.name, 'group_id': group_id.id})

            for request_line in request_line_ids:

                # first move, picking
                data = {
                    'name': group_id.name,
                    'state': 'confirmed',
                    'product_id': request_line.product_id.id,
                    'product_uom_qty': request_line.product_qty,
                    'product_uom': request_line.product_uom.id,
                    'location_id': picking_id.location_id.id,
                    'location_dest_id': picking_id.location_dest_id.id,
                    'procure_method': 'make_to_order' if request_line.purchase_line_id else 'make_to_stock',
                    'origin': doc.name,
                    'group_id': group_id.id,
                    'propagate': doc.propagate,
                    'unit_factor': 1,
                    'price_unit': request_line.price_unit,
                }
                stock_move = self.env['stock.move'].create(data)
                picking_id.move_lines |= stock_move

                request_line.move_id = stock_move

                if request_line.purchase_line_id:
                    request_line.purchase_line_id.write({'move_dest_ids': [(6, False, stock_move.ids)]})

                # second move, mo
                data = {
                    'name': group_id.name,
                    'state': 'confirmed',
                    'product_id': request_line.product_id.id,
                    'product_uom_qty': request_line.product_qty,
                    'product_uom': request_line.product_uom.id,
                    'location_id': doc.location_src_id.id,
                    'location_dest_id': stock_location_production.id,
                    'raw_material_production_id': doc.id,
                    'procure_method': 'make_to_order',
                    'origin': doc.name,
                    'group_id': group_id.id,
                    'propagate': doc.propagate,
                    'unit_factor': 1,
                    'price_unit': request_line.price_unit,
                    'move_orig_ids': [(6, False, stock_move.ids)]
                }
                mo_stock_move = self.env['stock.move'].create(data)
                doc.move_raw_ids |= mo_stock_move

            order_ids.button_confirm()

            # so_line = self.env['sale.order.line'].search([('request_line_id', 'in', request_line_ids.ids)])
            # for line in so_line:
            #     line.write({'move_ids': [(6, False, line.request_line_id.move_id.ids)]})

        return True

    @api.multi
    def action_assign_to_me(self):
        self.write({'responsible': self.env.user.id})

    def _purchase_count(self):
        return self.purchase_order_count + self.purchase_requisition_count

    ### ORM ###

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('material.request') or '/'
        return super(MaterialRequest, self).create(vals)






