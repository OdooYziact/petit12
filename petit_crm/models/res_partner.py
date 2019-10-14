# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    def _default_total_sales(self):
        """ do nothing """
        return 0

    def _default_scheduled_day(self):
        return self.env.ref('base_weekday.day_undefined').id or False


    annual_planned_visits = fields.Integer(string="Nombre de visites prévues pour l'année", required=False, default=0)
    monthly_planned_visits = fields.Integer(string="Nombre de visite", compute="_compute_planned_visits", store=False, readonly=True)

    trading_sales_target = fields.Integer(string="Objectif CA négoce", required=False, default=0)
    repair_sales_target = fields.Integer(string="Objectif CA réparation", required=False, default=0)

    total_sales = fields.Integer(string="CA réalisé", required=False, default=_default_total_sales, readonly=True)
    total_sales_y1 = fields.Integer(string="CA réalisé n-1", required=False, default=0)
    total_sales_y2 = fields.Integer(string="CA réalisé n-2", required=False, default=0)

    distance = fields.Integer(string="Distance (Km)", required=False, default=0)
    geographical_area = fields.Many2one(comodel_name="petit_crm.geographical_area", string="Secteur géographique", required=False)
    delivery_day = fields.Many2one(comodel_name='base.weekday', required=True, default=_default_scheduled_day,
                                   string='Delivery day', group_expand='_read_group_day_ids')

    temp_bl_chiffre = fields.Boolean(string="BL chiffré",  default=False)
    temp_condition_devis = fields.Char(string="Durée validité devis", required=False)
    temp_delai_relance = fields.Integer(string="Délai Relance", required=False, default=0)

    fax = fields.Char(string="Fax")

    @api.multi
    @api.depends('annual_planned_visits')
    def _compute_planned_visits(self):
        for partner in self:
            partner.monthly_planned_visits = (365 / partner.annual_planned_visits) if partner.annual_planned_visits else 0



