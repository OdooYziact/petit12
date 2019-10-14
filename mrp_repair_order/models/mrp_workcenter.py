# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    approval = fields.Boolean('Approval needed', default=False)