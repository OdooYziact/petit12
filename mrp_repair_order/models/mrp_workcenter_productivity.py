# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    origin = fields.Char(related='workorder_id.production_id.name', readonly=True, store=True, string="Origine")
    operation_id = fields.Many2one(related='workorder_id.operation_id', readonly=True, store=True, string="Opération")