# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _, modules
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def activity_user_count(self):
        """
        Ajout du fait qu'on ne compte pas les activites archivees, pour le total en haut de chaque page
        """
        query = """SELECT m.name, count(*), act.res_model as model,
                            CASE
                                WHEN now()::date - act.date_deadline::date = 0 Then 'today'
                                WHEN now()::date - act.date_deadline::date > 0 Then 'overdue'
                                WHEN now()::date - act.date_deadline::date < 0 Then 'planned'
                            END AS states
                        FROM mail_activity AS act
                        JOIN ir_model AS m ON act.res_model_id = m.id
                        WHERE user_id = %s AND archived IS NOT TRUE
                        GROUP BY m.name, states, act.res_model;
                        """
        self.env.cr.execute(query, [self.env.uid])
        activity_data = self.env.cr.dictfetchall()

        user_activities = {}
        for activity in activity_data:
            if not user_activities.get(activity['model']):
                user_activities[activity['model']] = {
                    'name': activity['name'],
                    'model': activity['model'],
                    'icon': modules.module.get_module_icon(self.env[activity['model']]._original_module),
                    'total_count': 0, 'today_count': 0, 'overdue_count': 0, 'planned_count': 0,
                }
            user_activities[activity['model']]['%s_count' % activity['states']] += activity['count']
            if activity['states'] in ('today', 'overdue'):
                user_activities[activity['model']]['total_count'] += activity['count']

        return list(user_activities.values())

