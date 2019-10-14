# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
import logging

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sign = fields.Binary(string="Sign")
    delivery_day = fields.Many2one(related='partner_id.delivery_day', readonly=True, string='Partner delivery day')
    is_signed = fields.Boolean(string="Signed", compute='_compute_sign', default=True)
    is_priority = fields.Boolean(string="Priority", default=False)
    priority = fields.Char(compute='_compute_priority')
    reception_person = fields.Many2one(comodel_name='res.partner', string="Received by")
    delivery_ref = fields.Char(string="Delivery Reference")
    carrier_type = fields.Selection(related='carrier_id.carrier_type', readonly=True, string='Type de transport')


    @api.depends('is_priority')
    @api.multi
    def _compute_priority(self):
        for record in self:
            record.priority = 'requested date' if record.is_priority else ''

    @api.depends('sign')
    @api.multi
    def _compute_sign(self):
        for record in self:
            record.is_signed = bool(record.sign)

    @api.depends('scheduled_day')
    @api.multi
    def _compute_scheduled_day(self):
        for record in self:
            record.scheduled_date = record._get_scheduled_date()

    @api.onchange('scheduled_day')
    def _onchange_scheduled_day(self):
        return {'value': {'scheduled_date': self._get_scheduled_date()}}

    @api.onchange('scheduled_date')
    def _onchange_scheduled_date(self):
        res = self._set_scheduled_day()
        if res != self.scheduled_day:
            self.scheduled_day = res

    def _set_scheduled_day(self):
        weekday = fields.Datetime.from_string(self.scheduled_date).weekday() + 1
        if weekday != self.scheduled_day.weekday:
            res = self.env['base.weekday'].search([('weekday', '=', weekday)], limit=1)
            return res.id if len(res) else self.env.ref('base_weekday.day_undefined').id or False

        return self.scheduled_day

    def _get_scheduled_date(self):
        if not self.scheduled_day.weekday:
            return self.scheduled_date

        now = datetime.today()
        weekday = now.weekday() + 1

        if self.scheduled_day.weekday == weekday:
            return now
        elif self.scheduled_day.weekday > weekday:
            rel = self.scheduled_day.weekday - weekday
            return now + timedelta(rel)
        else:
            rel = 7 - (weekday - self.scheduled_day.weekday)
            return now + timedelta(rel)

    @api.model
    def _read_group_day_ids(self, days, domain, order):
        days = self.env['base.weekday'].search([], order='sequence')
        return days

    def _default_scheduled_day(self):
        return self.env.ref('base_weekday.day_undefined', raise_if_not_found=False).id or False

    scheduled_day = fields.Many2one(comodel_name='base.weekday', required=True, default=_default_scheduled_day,
                                    readonly=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                    string='Scheduled day', group_expand='_read_group_day_ids')

    responsible = fields.Many2one('res.users', string='Responsible', track_visibility="onchange",
                                  readonly=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    @api.multi
    def action_assign_to_me(self):
        self.write({'responsible': self.env.user.id})

    @api.model
    def cron_dropshipping_auto_validate(self):
        """
        # Today is the day your dropshipping are delivered \o/
        # In the dropshing ways the piking is directly set in ready state but
        # there is no reservation, cause it don't need one
        # therefore it will raise an error if you don't process the quantity_done by hand (using the button_validate)
        # In order to bypass, we will use the normal formal Odoo picking way, you confirm, you assign then you done
        # The assign will reserve a quant_id, that the done action will be able te use to process the quantity_done
        :return: True or not
        """
        picking_id = self.env.ref('stock_dropshipping.picking_type_dropship', raise_if_not_found=False).id or False
        if not picking_id:
            _logger.warning(_('Dropshipping picking type id missing'))
            return False

        pickings = self.search([
            ('scheduled_date', '>=', datetime.strftime(datetime.combine(datetime.today(), time(0,0,0)), DEFAULT_SERVER_DATETIME_FORMAT)),
            ('scheduled_date', '<=', datetime.strftime(datetime.combine(datetime.today(), time(23,59,59)), DEFAULT_SERVER_DATETIME_FORMAT)),
            ('picking_type_id', '=', picking_id)
        ])
        if pickings:
            pickings.action_confirm() # is that usefull ? should test with and without
            pickings.action_assign()
            pickings.action_done()

        return True