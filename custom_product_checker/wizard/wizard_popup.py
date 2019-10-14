# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductWizardPopup(models.TransientModel):
    _name = 'product.wizard.popup'
    
    def get_message(self):
        return self._context.get('message', 'no message')
    
    message = fields.Text(default=get_message, readonly=True)
