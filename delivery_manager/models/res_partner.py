# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    def _default_scheduled_day(self):
        return self.env.ref('base_weekday.day_undefined').id or False

    delivery_day = fields.Many2one(comodel_name='base.weekday', required=True, default=_default_scheduled_day,
                                    readonly=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                    string='Delivery day', group_expand='_read_group_day_ids')

    # delivery_day = fields.Selection(string="Delivery day",
    #                          selection=[('Mon', 'Monday'),
    #                                     ('Tue', 'Tuesday'),
    #                                     ('Wed', 'Wednesday'),
    #                                     ('Thu', 'Thursday'),
    #                                     ('Fri', 'Friday'),
    #                                     ('Sat', 'Saturday'),
    #                                     ('undefined', 'Undefined')],
    #                          required=False,
    #                          default="undefined")




