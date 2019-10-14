# -*- coding: utf-8 -*-

from odoo import fields, models,  _
# from odoo.exceptions import UserError, AccessError, ValidationError
# from odoo.tools.safe_eval import safe_eval


class BaseWeekday(models.Model):
    _name = 'base.weekday'
    _description = 'Weekday'
    _order = 'sequence'

    name = fields.Char(string='Day', required=True, translate=True)
    weekday = fields.Integer(string='Weekday', required=False)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)

    fold = fields.Boolean(string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')