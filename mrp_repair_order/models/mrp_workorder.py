# -*- coding: utf-8 -*-

from datetime import datetime,timedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero
# from odoo.exceptions import UserError, ValidationError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    ### INHERITS ###
    duration_expected = fields.Float(states={'done': [('readonly', False)], 'cancel': [('readonly', False)]})

    ### ADDS ###
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approval', 'Waiting approval'),
        ('ready', 'Ready'),
        ('progress', 'In Progress'),
        ('done', 'Finished'),
        ('cancel', 'Cancelled')], string='Status',
        default='pending')
    partner_name = fields.Char(string="Customer", related="production_id.repair_order_id.partner_id.name")
    specification_ids = fields.One2many("mrp.repair.data","Specification", related="production_id.repair_order_id.specification_ids")
    title = fields.Char(related='current_quality_check_id.title')
    tolerance_min = fields.Float(related='current_quality_check_id.tolerance_min')
    tolerance_max = fields.Float(related='current_quality_check_id.tolerance_max')
    comment = fields.Html()
    request_line_ids = fields.One2many(related='production_id.request_line_ids')
    move_raw_ids = fields.One2many(related='production_id.move_raw_ids', readonly=True)
    # note = fields.Text('Description')
    specifications = fields.Char(related="production_id.repair_order_id.specifications")
    operation_note = fields.Text('Operation Note', related='operation_id.note', readonly=True)

    @api.multi
    def record_production(self):
        self.ensure_one()
        super(MrpWorkorder, self).record_production()

        if self.production_id.repair_order_id:
            if self.next_work_order_id.operation_id.expertise:
                self.production_id.repair_order_id.action_expertise()

            if self.operation_id.expertise:
                self.production_id.repair_order_id.action_expertise_done()

        return True


    @api.multi
    def _update_state(self):
        self.filtered(lambda x: x.state in ('pending') and x.workcenter_id.approval).update({'state': 'approval'})
        return True


    @api.multi
    def action_cancel_workorder(self):
        self.filtered(lambda x: x.state not in ('done', 'cancel', 'progress')).action_cancel()
        return True

        # if any([x.state in ('done', 'cancel', 'progress') for x in self]):
        #     raise UserError(_('A Manufacturing Order is already done, in progress or cancelled!'))
        #
        # self.action_cancel()

    @api.multi
    def action_ready(self):
        self.filtered(lambda x: x.state in ('cancel', 'pending', 'approval')).update({'state': 'ready'})
        return True

    @api.multi
    def action_start(self):
        self.filtered(lambda x: x.state in ('pending', 'approval')).update({'state': 'ready'})
        return True


    def _prepare_worklog(self):
        return {
            'workorder_id': self.id,
            'workcenter_id': self.workcenter_id.id,
            'user_id': self.env.user.id,
            'loss_id': self.env.ref('mrp.block_reason7').id,
        }

    def _action_worklog(self, period=15):
        end = datetime.now()
        start = end - timedelta(minutes=period)
        vals = self._prepare_worklog()
        vals.update(date_start=start, date_end=end)
        self.time_ids |= self.time_ids.create(vals)
        return True

    @api.multi
    def action_worklog_15m(self):
        self.ensure_one()
        return self._action_worklog(15)

    @api.multi
    def action_worklog_30m(self):
        self.ensure_one()
        return self._action_worklog(30)


    def _prepare_for_sale(self):
        default_product_id = self.env.ref('mrp_repair_order.generic_repair_product_operation', raise_if_not_found=False).product_variant_id or False
        product_id = self.operation_id.product_tmpl_id.product_variant_id if self.operation_id.product_tmpl_id else default_product_id


        if product_id == default_product_id and self.name:
            # desc = "%s\n%s" % (self.name, self.note)
            desc = "%s" % (self.name)
        else:
            desc = "%s\n%s" % (product_id.name_get()[0][1], product_id.description_sale)

        return {
            'name': self.operation_id.name if self.operation_id else self.name,
            'note': self.operation_id.note if self.operation_id else self.note,
            'product_id': product_id,
            'description': desc,
            # PET-151: calc based on duration excepted
            # 'product_uom_qty':  sum(self.time_ids.mapped('duration')) if self.state in ('done') else self.duration_expected,
            'product_uom_qty':  self.duration_expected,
            'operation_id': self.operation_id if self.operation_id else False,
            'cost_hour': self.workcenter_id.costs_hour,
            'state': self.state,
        }

    def _prepare_for_report(self):
        techs = []

        for time in self.time_ids:
            if time.user_id and time.user_id.name not in techs and time.user_id.name != '':
                techs.append(time.user_id.name)


        vals = {
            'name': self.operation_id.name,
            'quantity':  self.duration if self.state in ('done') else self.duration_expected,
            'duration': self.duration if self.duration else 0.00,
            'state': self.state,
            'workcenter': self.workcenter_id.name,
            'costs_hour': self.workcenter_id.costs_hour if self.workcenter_id and self.workcenter_id.costs_hour else 0.00,
            'duration_expected': self.duration_expected if self.duration_expected else 0.00,
            'quality_check': [],
            'techs': techs,
        }

        if self.check_ids:
            vals['quality_check'] = [x._prepare_for_report() for x in self.check_ids]

        return vals

    @api.multi
    def button_start(self):
        self.ensure_one()
        res = super(MrpWorkorder, self).button_start()

        if self.operation_id.expertise:
            self.production_id.action_expertise()

        return res

    @api.multi
    def action_refresh(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'target': 'fullscreen',
            'flags': {
                'headless': True,
                'form_view_initial_mode': 'edit',
            },
        }

    def action_view_production(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'name': 'Réparation',
            "views": [[False, "form"], [False, "tree"]],
            'res_id': self.production_id.id,
            'target': 'main',
        }

    def action_next_wo(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder',
            'views': [[self.env.ref('quality_mrp.mrp_workorder_view_form_tablet').id, 'form']],
            'res_id': self.next_work_order_id.id,
            'target': 'fullscreen',
            'flags': {
                'form_view_initial_mode': 'edit',
                'clear_breadcrumbs': True,
                'headless': True,
            }
        }

    def action_tree_all(self):
        return {
            'type': 'ir.actions.act_window',
            'name':'Opérations',
            'res_model': 'mrp.workorder',
            'views': [[self.env.ref('mrp.mrp_production_workcenter_tree_view_inherit').id, 'tree'], [False, 'form']],
            'view_mode': 'tree,form',
            'res_id': self.next_work_order_id.id,
            'context':{'group_by': 'production_id', 'search_default_ready': 1, 'search_default_progress': 1},
            'clear_breadcrumbs': True,
            'target': 'main',
            'flags': {
                'form_view_initial_mode': 'edit',
                'headless': False
            }
        }

    @api.multi
    def action_create_material_request(self):
        self.ensure_one()

        action = self.env.ref('mrp_repair_order.action_material_request_form').read()[0]
        action['context'] = {'default_res_id': self.production_id.id, 'default_res_model': 'mrp.production'}
        return action

    @api.multi
    def action_view_material_request(self):
        self.ensure_one()

        # action = self.env.ref('mrp_repair_order.action_view_material_request_tree').read()[0]
        # action.update({
        #     'context': {'default_res_id': self.production_id.id, 'default_res_model': 'mrp.production'},
        #     'target': 'new',
        # })

        action = {
            'name': 'Approvisionnement',
            'type': 'ir.actions.act_window',
            'res_model': 'material.request.line',
            'view_mode': 'tree',
            "views": [[False, "tree"]],
            'domain': [('request_id', 'in', self.production_id.request_ids.ids)],
            'context': {'edit': False, 'noedit': True, 'create': False},
            'target': 'new',
            'clear_breadcrumbs': True,
        }

        return action


    def do_measure(self):
        self.ensure_one()
        point_id = self.current_quality_check_id.point_id
        digits = 0.01
        if float_is_zero(point_id.tolerance_max, precision_rounding=digits) \
                and float_is_zero(point_id.tolerance_min, precision_rounding=digits) \
                and float_is_zero(point_id.norm, precision_rounding=digits):
            return self.do_pass()
        else:
            return super(MrpWorkorder, self).do_measure()

        # if self.measure < point_id.tolerance_min or self.measure > point_id.tolerance_max:
        #     return self.do_fail()
        # else:
        #     return self.do_pass()

    def do_finish(self):
        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id \
                and self.production_id.workorder_ids[0].id == self.id:
            if self.production_id.repair_order_id and self.production_id.repair_order_id.lot_id:
                self.final_lot_id = self.production_id.repair_order_id.lot_id

            # self.final_lot_id = self.env['stock.production.lot'].create({
            #     'product_id': self.production_id.product_id.id,
            # })

        self.record_production()

        if self.next_work_order_id.state != "ready":
            action = self.action_view_production()
        else:
            if not self.production_id.is_expertise_done:
                if self.next_work_order_id.operation_id.expertise or self.operation_id.expertise:
                    action = self.action_tree_all()
                else:
                    action = self.action_next_wo()

            else:
                if self.next_work_order_id.workcenter_id.id == self.workcenter_id.id:
                    action = self.action_next_wo()
                else:
                    action = self.action_tree_all()

        return action

    @api.model
    def create(self, vals):
        res = super(MrpWorkorder, self).create(vals)

        if self.env.context.get('fix_next_work_order', False):
            workorder_ids = self.env['mrp.workorder'].search([('production_id', '=', res.production_id.id)])
            if len(workorder_ids) > 1:
                workorder_ids[-2].next_work_order_id = res.id

        return res
