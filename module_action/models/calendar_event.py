# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _, modules
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime

class CalendarEvent(models.Model):
    _inherit = ['calendar.event']

    company_activity_id = fields.Many2one('res.partner', string="Société",domain="[('company_type','=','company')]", store=True) # Societe liee
    contact_activity_id = fields.Many2one('res.partner', string="Contact",domain="[('company_type','=','person'), ('parent_id','=',company_activity_id)]", store=True) # Contact lie
    activity_archived = fields.Boolean(compute='_compute_activity_button')
    activity_exist = fields.Boolean(compute='_compute_activity_button', default=False)

    @api.multi
    def _compute_activity_button(self):
        for event in self:
            activity = self.env['mail.activity'].search([('summary', '=', event.name),('calendar_event_id', '=', event.id), ('date_deadline', '=', event.start_datetime)], limit=1)
            if activity:
                event.activity_archived = activity.archived
                event.activity_exist = True
            else:
                event.activity_exist = False

    @api.model
    def create(self, values):
        """
        Creation d'une activite si un evenement est cree avec une societe et/ou un contact, ajout d'un participant si la creation vient d'une activite
        """
        if not values.get('activity_ids'):
            defaults = self.default_get(['activity_ids', 'res_model_id', 'res_id', 'user_id'])
            res_model_id = values.get('res_model_id', defaults.get('res_model_id'))
            res_id = values.get('res_id', defaults.get('res_id'))
            if not defaults.get('activity_ids') and not res_model_id and not res_id:
                if values.get('company_activity_id') or values.get('contact_activity_id'):
                    res_model_id = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1).id

                if values.get('contact_activity_id'):
                    res_id = values.get('contact_activity_id')
                else:
                    res_id = values.get('company_activity_id')
                values['res_id'] = res_id
                values['res_model_id'] = res_model_id
                values['res_model'] = 'res.partner'
        if values.get('company_activity_id') or values.get('contact_activity_id'):
            if values.get('contact_activity_id'):
                values['res_id'] = values.get('contact_activity_id')
            else:
                values['res_id'] = values.get('company_activity_id')

            values['res_model_id'] = self.env['ir.model'].search([('model', '=', 'res.partner')]).id
            values['res_model'] = 'res.partner'

        result = super(CalendarEvent, self).create(values)

        return result

    def end_activity(self):
        """
        Ouvre la vue pour entrer un feedback, depuis le formulaire de la tree view
        """
        activity = self.env['mail.activity'].search([('calendar_event_id', '=', self.id)])

        view_id = self.env.ref('module_action.mail_activity_form_feedback').id

        if activity[0] and activity[0].archived == False:
            return {
                "type": 'ir.actions.act_window',
                "name": 'Activités',
                "res_model": 'mail.activity',
                "view_mode": 'form',
                "view_type": 'form',
                "views": [[view_id, 'form']],
                'res_id': activity[0].id,
                "view_id": view_id,
                "target": 'new',
            }
        else:
            raise UserError(_("L'activité est déjà archivée."))

    # Deux methodes pour mettre les coordonnees de la societe ou du contact en description, et changer cette derniere en fonction des modifications
    @api.onchange('contact_activity_id')
    def onchange_contact_coordonnees(self):
        country_name = ''

        # Si le contact a change ou a ete ajoute
        if self.contact_activity_id:
            if self.contact_activity_id.country_id:
                country_name = self.env['res.country'].search([('id', '=', self.contact_activity_id.country_id.id)])
                country_name = country_name[0].name

            string_to_add = '%s\n%s - %s\n%s\n%s %s\n%s %s\n%s\n__________\n' % (self.contact_activity_id.name or '',
                                                                                 self.contact_activity_id.phone or '',
                                                                                 self.contact_activity_id.mobile or '',
                                                                                 self.contact_activity_id.email or '',
                                                                                 self.contact_activity_id.street or '',
                                                                                 self.contact_activity_id.street2 or '',
                                                                                 self.contact_activity_id.zip or '',
                                                                                 self.contact_activity_id.city or '',
                                                                                 country_name or '')
            desc = self.description
            if self.description == False:
                desc = ['', '']
            else:
                desc = self.description.split('__________')

            if len(desc) == 1:
                self.description = '%s%s' % (string_to_add, desc[0])
            elif len(desc) > 1:
                self.description = '%s%s' % (string_to_add, desc[1])

        # Si le contact est supprime
        elif not self.contact_activity_id:
            # Suppression si pas de societe
            if not self.company_activity_id:
                string_to_add = ' \n__________\n'
            # Si societe, description de la societe
            elif self.company_activity_id:
                if self.company_activity_id.country_id:
                    country_name = self.env['res.country'].search([('id', '=', self.company_activity_id.country_id.id)])
                    country_name = country_name[0].name

                string_to_add = '%s\n%s - %s\n%s\n%s %s\n%s %s\n%s\n__________\n' % (
                self.company_activity_id.name or '',
                self.company_activity_id.phone or '',
                self.company_activity_id.mobile or '',
                self.company_activity_id.email or '',
                self.company_activity_id.street or '',
                self.company_activity_id.street2 or '',
                self.company_activity_id.zip or '',
                self.company_activity_id.city or '',
                country_name or '')

            desc = self.description
            if self.description == False:
                desc = ['', '']
            else:
                desc = self.description.split('__________')

            if len(desc) == 1:
                self.description = '%s%s' % (string_to_add, desc[0])
            elif len(desc) > 1:
                self.description = '%s%s' % (string_to_add, desc[1])


    @api.onchange('company_activity_id')
    def onchange_company_coordonnees(self):
        self.contact_activity_id = False
        country_name = ''
        # Description de la societe
        if self.company_activity_id:
            if self.company_activity_id.country_id:
                country_name = self.env['res.country'].search([('id', '=', self.company_activity_id.country_id.id)])
                country_name = country_name[0].name

            string_to_add = '%s\n%s - %s\n%s\n%s %s\n%s %s\n%s\n__________\n' % (self.company_activity_id.name or '',
                                                                                 self.company_activity_id.phone or '',
                                                                                 self.company_activity_id.mobile or '',
                                                                                 self.company_activity_id.email or '',
                                                                                 self.company_activity_id.street or '',
                                                                                 self.company_activity_id.street2 or '',
                                                                                 self.company_activity_id.zip or '',
                                                                                 self.company_activity_id.city or '',
                                                                                 country_name or '')
            desc = self.description
            if self.description == False:
                desc = ['', '']
            else:
                desc = self.description.split('__________')

            if len(desc) == 1:
                self.description = '%s%s' % (string_to_add, desc[0])
            elif len(desc) > 1:
                self.description = '%s%s' % (string_to_add, desc[1])
        # Si suppression de la societe, suppression de la description
        elif not self.company_activity_id:
            string_to_add = ' \n__________\n'
            desc = self.description
            if self.description == False:
                desc = ['', '']
            else:
                desc = self.description.split('__________')

            if len(desc) == 1:
                self.description = '%s%s' % (string_to_add, desc[0])
            elif len(desc) > 1:
                self.description = '%s%s' % (string_to_add, desc[1])

    # Lorsqu'un contact ou la societe change, changement de l'activite (supprimer, modifier le partner...)
    @api.multi
    def write(self, values):
        # Si modification sur la societe ou le contact
        if 'company_activity_id' in values or 'contact_activity_id' in values:
            activity = self.env['mail.activity'].search([('res_model', '=', 'res.partner'), ('summary', '=', self.name),('calendar_event_id', '=', self.id), ('archived', '=', False)], limit=1)
            activity_not_partner = self.env['mail.activity'].search([('res_model', '!=', 'res.partner'), ('summary', '=', self.name),('calendar_event_id', '=', self.id), ('archived', '=', False)], limit=1)

            if activity:
                # Ajout ou changement du contact
                if 'contact_activity_id' in values and values.get('contact_activity_id') != False:
                    activity.write({'res_id': values.get('contact_activity_id')})
                    self.res_id = values.get('contact_activity_id')
                    self.res_model = 'res.partner'
                    self.res_model_id = self.env['ir.model'].search([('model', '=', 'res.partner')]).id
                # Suppression du contact
                elif 'contact_activity_id' in values and values.get('contact_activity_id') == False:
                    # Ajout/modification d'une societe
                    if 'company_activity_id' in values and values.get('company_activity_id') != False:
                        activity.write({'res_id': values.get('company_activity_id')})
                        self.res_id = values.get('company_activity_id')
                        self.res_model = 'res.partner'
                        self.res_model_id = self.env['ir.model'].search([('model', '=', 'res.partner')]).id
                    # Suppression de la societe
                    elif 'company_activity_id' in values and values.get('company_activity_id') == False:
                        activity.write({'calendar_event_id': False})
                        activity.unlink()
                        if activity_not_partner:
                            self.res_id = activity_not_partner.res_id
                            self.res_model = activity_not_partner.res_model
                            self.res_model_id = activity_not_partner.res_model_id
                        else:
                            self.res_id = False
                            self.res_model = False
                            self.res_model_id = False
                    # Pas d'ajout/modification ou de suppression de societe, et pas de societe avant
                    elif 'company_activity_id' not in values and not self.company_activity_id:
                        activity.write({'calendar_event_id': False})
                        activity.unlink()
                        if activity_not_partner:
                            self.res_id = activity_not_partner.res_id
                            self.res_model = activity_not_partner.res_model
                            self.res_model_id = activity_not_partner.res_model_id
                        else:
                            self.res_id = False
                            self.res_model = False
                            self.res_model_id = False
                    # Pas d'ajout/modification ou de suppression de societe, et societe deja presente
                    elif 'company_activity_id' not in values and self.company_activity_id:
                        activity.write({'res_id': self.company_activity_id})
                        self.res_id = self.company_activity_id
                        self.res_model = 'res.partner'
                        self.res_model_id = self.env['ir.model'].search([('model', '=', 'res.partner')]).id
                # Pas de contact touche et suppression de la societe
                elif 'contact_activity_id' not in values and 'company_activity_id' in values and values.get('company_activity_id') == False:
                    activity.write({'calendar_event_id': False})
                    activity.unlink()
                    if activity_not_partner:
                        self.res_id = activity_not_partner.res_id
                        self.res_model = activity_not_partner.res_model
                        self.res_model_id = activity_not_partner.res_model_id
                    else:
                        self.res_id = False
                        self.res_model = False
                        self.res_model_id = False
                # Pas de contact touche et ajout/modification de societe
                elif 'contact_activity_id' not in values and 'company_activity_id' in values and values.get('company_activity_id') != False:
                    activity.write({'res_id': values.get('company_activity_id')})
                    self.res_id = values.get('company_activity_id')
                    self.res_model = 'res.partner'
                    self.res_model_id = self.env['ir.model'].search([('model', '=', 'res.partner')]).id
                else:
                    pass
            else:
                # Si pas d'activite auparavant, la creer
                val = {}

                meeting_activity_type = self.env['mail.activity.type'].search([('category', '=', 'meeting')],limit=1)
                model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)[0]

                val['res_model_id'] = model.id
                val['res_model'] = 'res.partner'
                val['activity_type_id'] = meeting_activity_type[0].id

                if 'name' in values:
                    val['summary'] = values.get('name')
                else:
                    val['summary'] = self.name

                if 'description' in values:
                    val['note'] = values.get('description')
                else:
                    val['note'] = self.description

                if 'start_datetime' in values:
                    val['date_deadline'] = values.get('start_datetime')
                else:
                    val['date_deadline'] = self.start_datetime

                if 'user_id' in values:
                    val['user_id'] = values.get('user_id')
                else:
                    val['user_id'] = self.user_id.id

                val['calendar_event_id'] = self.id

                val['archived'] = False


                if 'contact_activity_id' in values:
                    contact = self.env['res.partner'].search([('id', '=', values.get('contact_activity_id'))])[0]
                    val['res_id'] = values.get('contact_activity_id')
                    val['res_name'] = contact.name
                    res = self.env['mail.activity'].create(val)
                    values['res_id'] = values.get('contact_activity_id')
                elif 'company_activity_id' in values:
                    company = self.env['res.partner'].search([('id', '=', values.get('company_activity_id'))])[0]
                    val['res_id'] = values.get('company_activity_id')
                    val['res_name'] = company.name
                    res = self.env['mail.activity'].create(val)
                    values['res_id'] = values.get('company_activity_id')

                values['activity_ids'] = [(6, 0, [res.id])]

                values['res_model'] = 'res.partner'
                values['res_model_id'] = self.env['ir.model'].search([('model', '=', 'res.partner')]).id

        result = super(CalendarEvent, self).write(values)

        return result
