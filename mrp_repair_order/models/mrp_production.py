# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    ### INHERITS ###
    workorder_ids = fields.One2many(readonly=True)
    state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('waiting', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default='confirmed', track_visibility='onchange')

    ### NEW ###
    repair_order_id = fields.Many2one(comodel_name='mrp.repair.order', string='Repair order', required=False, ondelete='cascade')
    repair_step = fields.Selection(related='repair_order_id.step', default="", readonly=True)
    comments = fields.Text(string='Comments')
    request_ids = fields.One2many(comodel_name='material.request', compute='_compute_material_request')
    request_count = fields.Integer(compute="_compute_material_request")
    request_line_ids = fields.One2many(comodel_name='material.request.line', compute='_compute_material_request')
    is_expertise_done = fields.Boolean(compute="_compute_expertise", readonly=True)
    # notes = fields.One2many(related='workorder_ids', string='Notes', readonly=True)
    notes = fields.One2many(comodel_name='mrp.workorder', compute='_compute_workorder_note', string='Notes')

    ### COMPUTE ###

    @api.depends('workorder_ids.note')
    @api.multi
    def _compute_workorder_note(self):
        for record in self:
            record.notes = record.workorder_ids.filtered(lambda rec: rec.comment)

    @api.depends('state', 'workorder_ids.state')
    @api.multi
    def _compute_material_request(self):
        for production in self:
            production.request_ids = self.env['material.request'].search([('res_id', '=', production.id), ('res_model', '=', 'mrp.production')])
            production.request_count = len(production.request_ids)
            production.request_line_ids = production.request_ids.mapped('request_line').ids

    @api.multi
    def _compute_expertise(self):
        for production in self:
            production.is_expertise_done = True if any(production.workorder_ids.filtered(lambda x: x.operation_id.expertise and x.state == 'done')) else False

    @api.multi
    def _compute_estimated_cost(self):
        res = []
        for record in self:
            operations = 0.0
            raw_material = 0.0

            for wo in record.workorder_ids.filtered(lambda x: x.state not in ('cancel')):
                duration = sum(wo.time_ids.mapped('duration')) if wo.state in ('done') else wo.duration_expected
                operations += (duration / 60) * wo.workcenter_id.costs_hour

            for move_raw in record.move_raw_ids:
                raw_material += abs(move_raw.product_qty * move_raw.price_unit)

            res.append({'operations': operations, 'raw_material': raw_material})
        return res

    ### ACTION ###

    @api.multi
    def action_waiting(self):
        return self.update({'state': 'waiting'})

    @api.multi
    def action_in_progress(self):
        for record in self:
            if record.workorder_ids.mapped('final_lot_id'):
                record.workorder_ids.filtered(lambda x: not x.final_lot_id).update({
                    'final_lot_id': record.workorder_ids.mapped('final_lot_id')[0]
                })
        return self.update({'state': 'progress'})

    @api.multi
    def action_refresh(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.multi
    def action_view_repair_order(self):
        action = {
            "type": "ir.actions.act_window",
            "name": "Réparation",
            "res_model": "mrp.repair.order",
            "res_id": self.repair_order_id.id,
            "view_type": 'form',
            "views": [[False, "form"], [False, "tree"]],
            "target": 'current',
        }

        return action

    @api.multi
    def action_consume(self):
        return self._consume_move_raw_ids()

    @api.multi
    def action_end(self):
        if self.workorder_ids.filtered(lambda x: x.state in ('pending', 'ready', 'approval')).action_cancel():
            return self.write({'state': 'done'})
        return True

    @api.multi
    def action_expertise(self):
        self.mapped('repair_order_id').action_expertise()
        return True

    @api.multi
    def action_expertise_done(self):
        self.mapped('repair_order_id').action_expertise_done()
        return True

    @api.multi
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.env['stock.picking'].search([('group_id', 'in', self.mapped('procurement_group_id').ids)])
        action['domain'] = [('id', 'in', pickings.ids)]

        # elif pickings:
        #     action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
        #     action['res_id'] = pickings.id
        return action

    @api.multi
    def action_add_raw_move_from_request(self):
        """
        Ajoute les lignes de demandes de fournitures aux matières premières
        :return: stock move
        """
        for record in self:
            moves = self.env['stock.move']
            # TODO: check if request line previously added in raw moves
            for request_line in record.request_line_ids.filtered(lambda x: x.is_done):
                moves += record._add_raw_move(request_line)
            return moves

    ### BUSINESS ###

    def _prepare_for_sale(self):
        return [workorder._prepare_for_sale() for workorder in self.workorder_ids.filtered(lambda x: x.state not in ('cancel'))]

    def _prepare_material_request_for_sale(self):
        return [line._prepare_for_sale() for line in self.request_line_ids.filtered(lambda x: x.active and x.state and x.state in ('done'))]

    def _consume_move_raw_ids(self):
        # automate product quantity used to produce

        # if any(self.filtered(lambda rec: rec.state in ('done', 'cancel'))):
        #     return False

        for record in self:
            lot_id = record.finished_move_line_ids[-1].lot_id if record.finished_move_line_ids else False
            move_ids = record.move_raw_ids.filtered(lambda rec: rec.state in ('assigned') and float_compare(rec.quantity_done,
                                                                              rec.product_uom_qty,
                                                                              precision_rounding=rec.product_uom.rounding) == -1)
            for move in move_ids:
                if lot_id:
                    for move_line in move.active_move_line_ids:
                        if float_compare(move_line.qty_done, move_line.product_qty, precision_rounding=move_line.product_uom.rounding) == -1:
                            move_line.write({'lot_produced_id': lot_id.id, 'qty_done': move_line.product_qty})

                    move._action_done()
                else:
                    move._action_done()

        return True

    def _prepare_workorders_for_report(self):
        return [workorder._prepare_for_report() for workorder in self.workorder_ids]

    def _prepare_materials_for_report(self):
        vals = []
        for stock_move in self.move_raw_ids:
            vals.append({
                'pname': stock_move.product_id.name_get()[0][1],
                # 'pcode': stock_move.product_id.default_code,
                'qty': stock_move.product_uom_qty,
                'uom': stock_move.product_uom.name,
                'pprice' : abs(stock_move.price_unit),
            })
        return vals

    def _add_raw_move(self, request_line):
        data = {
            # 'sequence': bom_line.sequence,
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            # 'bom_line_id': bom_line.id,
            'product_id': request_line.product_id.id,
            'product_uom_qty': request_line.product_qty,
            'product_uom': request_line.product_uom.id,
            'location_id': self.location_src_id.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': False,
            'price_unit': request_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': self.location_src_id.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': 1,
        }
        return self.env['stock.move'].create(data)

    def _get_lot_id(self, product_id):
        """
        Generate serial number (lot id) for product
        :param product_id:
        :return: recordset
        """
        return self.env['stock.production.lot'].create({
            'product_id': product_id.id,
        })

    ### INHERITS / OVERRIDE ###

    @api.multi
    def button_mark_done(self):
        # automate product quantity used to produce
        self._consume_move_raw_ids()

        res = super(MrpProduction, self).button_mark_done()
        return self.mapped('repair_order_id').action_repair_end()

    @api.multi
    def action_cancel(self):
        """
        Cancel material request
        :return:
        """
        self.mapped('request_ids').action_cancel()
        return super(MrpProduction, self).action_cancel()

    @api.multi
    @api.depends('workorder_ids')
    def _compute_workorder_count(self):
        # filter on cancel state
        data = self.env['mrp.workorder'].read_group([('production_id', 'in', self.ids), ('state', '!=', 'cancel')], ['production_id'], ['production_id'])
        count_data = dict((item['production_id'][0], item['production_id_count']) for item in data)
        for production in self:
            production.workorder_count = count_data.get(production.id, 0)

    # PET-133 Look for quality checks in work orders related the current production order
    @api.multi
    def action_view_quality_checks(self):
        truc = self.workorder_ids.mapped('check_ids')
        return {
            'name': 'Contrôle Qualité',
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check',
            'view_id': 'quality_check_view_tree',
            'view_mode': 'form',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('id', 'in', truc.ids)],
        }

    ### ORM ###

    @api.model
    def create(self, values):
        defaults = self.default_get(self._fields.keys())
        defaults.update(values)
        res = super(MrpProduction, self).create(defaults)

        return res
