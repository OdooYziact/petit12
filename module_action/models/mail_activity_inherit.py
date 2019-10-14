# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _, modules
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    archived = fields.Boolean(default=False) # Indique si l'activite est terminee
    sale_order_id = fields.Many2one('sale.order', string='Devis relié', compute='_compute_sale_order')
    sale_present = fields.Boolean(default=False, compute='_compute_sale_order', store=True)
    sale_order_partner = fields.Char(string='Client du devis', compute='_compute_sale_order')
    sale_order_name = fields.Char(string='Nom du devis', compute='_compute_sale_order')
    sale_order_amount = fields.Float(string='Montant du devis', compute='_compute_sale_order')
    sale_order_date = fields.Date(string='Date du devis', compute='_compute_sale_order')

    @api.depends('res_model', 'res_id', 'activity_type_id')
    @api.one
    def _compute_sale_order(self):
        type = self.env['mail.activity.type'].search([('id', '=', self.activity_type_id.id)])

        if type.name == 'Relance devis' and self.res_model == 'sale.order':
            so = self.env['sale.order'].search([('id', '=', self.res_id)])

            self.sale_order_id = so.id
            self.sale_present = True

            self.sale_order_partner = so.partner_id.name
            self.sale_order_amount = so.amount_total
            self.sale_order_name = so.name
            self.sale_order_date = so.date_order
        else:
            self.sale_order_id = False
            self.sale_present = False

            self.sale_order_partner = False
            self.sale_order_amount = False
            self.sale_order_name = False
            self.sale_order_date = False

    @api.multi
    def action_create_calendar_event(self):
        """
        Ajout de la société et/ou contact sur le calendrier
        """
        res = super(MailActivity, self).action_create_calendar_event()

        id_res = self.env['res.partner'].search([('id', '=', self.res_id)])

        if self.res_model == 'res.partner':
            if not id_res.parent_id:
                res['context']['default_company_activity_id'] = self.res_id
            else:
                res['context']['default_company_activity_id'] = id_res.parent_id.id
                res['context']['default_contact_activity_id'] = self.res_id

        return res

    def action_feedback(self, feedback=False):
        """
        :param feedback: feedback entre par l'utilisateur
        :return: une action de retour sur la vue precedente
        """
        self.archived = True

        self.feedback = feedback

        new_enr = self.copy() # Copie de l'activite avant sa suppression

        res = super(MailActivity, self).action_feedback(feedback)  # Etait return à la base

        events = new_enr.mapped('calendar_event_id')
        if feedback:
            for event in events:
                description = event.description
                tab_res = description.split('Feedback')
                description = '<p>%s</p>\n%s%s' % (tab_res[0] or '', _("Feedback: "), feedback)
                event.write({'description': description})

        if 'active_model' in self._context and self._context['active_model'] != 'calendar.event':
            form_id = self.env.ref('module_action.mail_activity_form_view_for_tree').id

            return {
                "type": 'ir.actions.act_window',
                "name": 'Activités',
                "res_model": 'mail.activity',
                "view_type": 'form',
                "view_mode": 'form',
                "views": [[form_id, 'form']],
                "views_id": {'ref': form_id},
                "view_id": {'ref': form_id},
                "res_id": new_enr.id,
                "target": 'current',
            }

            # return {'type': 'ir.actions.client', 'tag': 'reload'}

        return res

    def unlink_w_meeting(self):
        """
        Methode appelee en JS, ajout d'une verification du fait que l'enregistrement n'a pas deja ete supprime
        """
        res = ''
        events = self.mapped('calendar_event_id')
        if self.exists():
            res = self.unlink()
        if events.exists():
            events.unlink()
        return res

    @api.multi
    def unlink2(self):
        """
        Ajout de la suppression de l'evenement associe puis retour sur la vue precedente
        """
        self._check_access('unlink')

        for activity in self:
            if activity.date_deadline <= fields.Date.today():
                self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
                    {'type': 'activity_updated', 'activity_deleted': True})

            if activity.calendar_event_id != False and activity.archived != True:
                activity.calendar_event_id.unlink()

        if self.exists():
            res = super(MailActivity, self.sudo()).unlink()

        return {'type': 'ir.actions.client', 'tag': 'history_back'} or res

    def open_feedback_form(self):
        """
        Ouvre la vue pour entrer un feedback, depuis le formulaire de la tree view
        """
        view_id = self.env.ref('module_action.mail_activity_form_feedback').id
        return {
            "type": 'ir.actions.act_window',
            "name": 'Activités',
            "res_model": 'mail.activity',
            "view_mode": 'form',
            "view_type": 'form',
            "views": [[view_id, 'form']],
            'res_id': self.id,
            "view_id": view_id,
            "target": 'new',
        }

    @api.multi
    def action_done_with_feedback(self):
        """
        :return: une action de retour à la vue précédente
        """
        return self.action_feedback(self.feedback)

    @api.model
    def create(self, values):
        if values and not values.get('res_id') and self._context.get('default_res_id'):
            values['res_id'] = self._context.get('default_res_id')
        if values and not values.get('res_model_id') and self._context.get('default_res_model_id'):
            values['res_model_id'] = self._context.get('default_res_model_id')
        if values and not values.get('res_model') and self._context.get('default_res_model'):
            values['res_model'] = self._context.get('default_res_model')

        res = super(MailActivity, self).create(values)

        return res
