from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class PartnerReferences(models.Model):
    _name = "partner.references"
    _desc = 'Partner References'


    name = fields.Char(string='Reference', required=True, help='Partner reference name')
    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    required = fields.Boolean(default=True, help="Value required")
    note = fields.Text()


    _sql_constraints = [
        ('name_unique',
        'UNIQUE(name)',
        'Name must be unique.'),
    ]