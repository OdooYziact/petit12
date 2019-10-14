# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _

from odoo.tools.mimetypes import guess_mimetype
import base64


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'document.attachment']

