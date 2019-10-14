from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class PartnerPractices(models.Model):
    _name = 'partner.practices'
    _desc = 'Partner Practices'


    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique',
        'UNIQUE(name)',
        'Name must be unique.'),
    ]




