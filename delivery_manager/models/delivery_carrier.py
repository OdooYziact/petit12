# -*- coding: utf-8 -*-

# import logging

from odoo import models, fields, api, _
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
# _logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def _get_carrier_type(self):
        return [
            ('standard', 'Standard'),
            ('internal', 'Interne'),
            ('collect', 'Enlèvement sur place'),
            ('dropship', 'Livraison directe')
        ]

    carrier_type = fields.Selection(selection=_get_carrier_type, required=True, default='standard',
                                    string='Type de transport')
