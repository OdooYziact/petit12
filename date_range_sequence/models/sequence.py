# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class Sequence(models.Model):
    _inherit = 'ir.sequence'

    is_auto_date_range = fields.Boolean(string="Remplir automatiquement les intervalles de date", default=False)
    date_range_type_id = fields.Many2one(comodel_name="date.range.type", string="Type d'intervalle")

    @api.model
    def _get_date_range(self, type_id):
        """

        :param type_id:
        :return: []
        """
        date_range_ids = self.env['date.range'].search([('type_id', '=', type_id.id)])

        return [(x.date_start, x.date_end) for x in date_range_ids]


    @api.multi
    def action_auto_date_range(self):
        """
        Button
        :return:
        """
        date_range_env = self.env['ir.sequence.date_range']

        for sequence in self:
            if sequence.use_date_range and sequence.is_auto_date_range and sequence.date_range_type_id:
                date_range = sequence._get_date_range(sequence.date_range_type_id)

                for item in date_range:
                    res = date_range_env.sudo().create({
                        'date_from': item[0],
                        'date_to': item[1],
                        'number_next_actual': 1,
                        'sequence_id': sequence.id,
                    })
            else:
                raise UserError("Aucun intervalle de date disponible.")

        return True

    @api.multi
    def action_view_date_range(self):
        """

        :return: view
        """
        self.ensure_one()

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Intervalles de date',
            'res_model': 'date.range',
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            'context': {
                'search_default_is_open': True,
            }
        }

        return action

