# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class GeographicalArea(models.Model):
    _name = "petit_crm.geographical_area"

    name = fields.Char(string="Secteur", required=True)
