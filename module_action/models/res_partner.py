# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _, modules
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime

class ResPartner(models.Model):
    _inherit = 'res.partner'

    activities_count = fields.Integer(compute='_activities_count') # Nombre d'activites total
    activities_count_current = fields.Integer(compute='_activities_count') # Nombre d'activites en cours

    @api.one
    def _activities_count(self):
        """
        Calcul pour le bouton dans les fiches client
        Si le partner est une societe, on compte les resultats des ses contacts egalement
        """
        if self.parent_id:
            sale_order = self.env['sale.order'].search([('partner_id', '=', self.id)]).ids  # Devis/bons de commande
            crm_lead = self.env['crm.lead'].search([('partner_id', '=', self.id)]).ids  # Opportunites

            activities_society = self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model', '=', 'res.partner')])  # Liees à la societe
            activities_order = self.env['mail.activity'].search([('res_id', 'in', sale_order), ('res_model', '=', 'sale.order')])  # Liees aux devis/bons de commande
            activities_lead = self.env['mail.activity'].search([('res_id', 'in', crm_lead), ('res_model', '=', 'crm.lead')])  # Liees aux opportunites

            # Equivalent avec seulement les activites en cours
            activities_society_current = self.env['mail.activity'].search([('archived', '!=', True), ('res_id', '=', self.id), ('res_model', '=', 'res.partner')])
            activities_order_current = self.env['mail.activity'].search([('archived', '!=', True), ('res_id', 'in', sale_order), ('res_model', '=', 'sale.order')])
            activities_lead_current = self.env['mail.activity'].search([('archived', '!=', True), ('res_id', 'in', crm_lead), ('res_model', '=', 'crm.lead')])

            self.activities_count = len(activities_society) + len(activities_order) + len(activities_lead)
            self.activities_count_current = len(activities_society_current)  + len(activities_order_current) + len(activities_lead_current)
        else:
            children = self.env['res.partner'].search([('parent_id', '=', self.id)]).ids # Contacts
            sale_order = self.env['sale.order'].search(['|', ('partner_id', '=', self.id), ('partner_id', 'in', children)]).ids # Devis/bons de commande
            crm_lead = self.env['crm.lead'].search(['|', ('partner_id', '=', self.id), ('partner_id', 'in', children)]).ids # Opportunites

            activities_society = self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model', '=', 'res.partner')]) # Liees à la societe
            activities_children = self.env['mail.activity'].search([('res_id', 'in', children), ('res_model', '=', 'res.partner')]) # Liees aux contacts
            activities_order = self.env['mail.activity'].search([('res_id', 'in', sale_order), ('res_model', '=', 'sale.order')]) # Liees devis/bons de commande
            activities_lead = self.env['mail.activity'].search([('res_id', 'in', crm_lead), ('res_model', '=', 'crm.lead')]) # Liees aux opportunites

            # Equivalent avec seulement les activites en cours
            activities_society_current = self.env['mail.activity'].search([('archived', '!=', True), ('res_id', '=', self.id), ('res_model', '=', 'res.partner')])
            activities_children_current = self.env['mail.activity'].search([('archived', '!=', True), ('res_id', 'in', children), ('res_model', '=', 'res.partner')])
            activities_order_current = self.env['mail.activity'].search([('archived', '!=', True), ('res_id', 'in', sale_order), ('res_model', '=', 'sale.order')])
            activities_lead_current = self.env['mail.activity'].search([('archived', '!=', True), ('res_id', 'in', crm_lead), ('res_model', '=', 'crm.lead')])

            self.activities_count = len(activities_society) + len(activities_children) + len(activities_order) + len(activities_lead)
            self.activities_count_current = len(activities_society_current) + len(activities_children_current) + len(activities_order_current) + len(activities_lead_current)

    @api.multi
    def mail_activity_tree_view_action(self):
        """
        Ouverture de la tree view depuis le bouton des fiches clients
        """
        id_doc = self.id
        form_id = self.env.ref('module_action.mail_activity_form_view_for_tree').id

        if self.parent_id:
            sale_order = self.env['sale.order'].search([('partner_id', '=', self.id)]).ids  # Devis/bons de commande
            crm_lead = self.env['crm.lead'].search([('partner_id', '=', self.id)]).ids  # Opportunites

            activities_society = self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model', '=', 'res.partner')]).ids  # Liees à la societe
            activities_order = self.env['mail.activity'].search([('res_id', 'in', sale_order), ('res_model', '=', 'sale.order')]).ids  # Liees devis/bons de commande
            activities_lead = self.env['mail.activity'].search([('res_id', 'in', crm_lead), ('res_model', '=', 'crm.lead')]).ids  # Liees aux opportunites

            return {
                "type": 'ir.actions.act_window',
                "name": 'Activités',
                "res_model": 'mail.activity',
                "view_type": 'form',
                "view_mode": 'list',
                "views": [[False, 'list'], [form_id, 'form']],
                "context": {
                    'search_default_currently': 1,
                    'search_default_mine': 1,
                    'res_model': 'res.partner',
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1).id,
                    'res_id': self.id,
                },
                "views_id": {'ref': 'mail_activity_tree_view_action'},
                "view_id": {'ref': 'mail_activity_tree_view_action'},
                'domain': ['|', '|', ('id', 'in', activities_society), ('id', 'in', activities_order), ('id', 'in', activities_lead)],
                "target": 'current',
            }
        else:
            children = self.env['res.partner'].search([('parent_id', '=', self.id)]).ids  # Contacts
            sale_order = self.env['sale.order'].search(['|', ('partner_id', '=', self.id), ('partner_id', 'in', children)]).ids  # Devis/bons de commande
            crm_lead = self.env['crm.lead'].search(['|', ('partner_id', '=', self.id), ('partner_id', 'in', children)]).ids  # Opportunites

            activities_society = self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model', '=', 'res.partner')]).ids  # Liees à la societe
            activities_children = self.env['mail.activity'].search([('res_id', 'in', children), ('res_model', '=', 'res.partner')]).ids  # Liees aux contacts
            activities_order = self.env['mail.activity'].search([('res_id', 'in', sale_order), ('res_model', '=', 'sale.order')]).ids  # Liees devis/bons de commande
            activities_lead = self.env['mail.activity'].search([('res_id', 'in', crm_lead), ('res_model', '=', 'crm.lead')]).ids  # Liees aux opportunites

            return {
                "type": 'ir.actions.act_window',
                "name": 'Activités',
                "res_model": 'mail.activity',
                "view_type": 'form',
                "view_mode": 'list',
                "views": [[False, 'list'],[form_id, 'form']],
                "context": {
                    'search_default_currently': 1,
                    'search_default_mine': 1,
                    'default_res_model': 'res.partner',
                    'default_res_model_id': self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1).id,
                    'default_res_id': self.id,
                },
                "views_id": {'ref': 'mail_activity_tree_view_action'},
                "view_id": {'ref': 'mail_activity_tree_view_action'},
                'domain':['|','|','|',('id', 'in', activities_society), ('id', 'in', activities_children), ('id', 'in', activities_order), ('id', 'in', activities_lead)],
                "target": 'current',
            }
