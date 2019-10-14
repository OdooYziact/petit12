from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)


class CustomPopup(models.AbstractModel):
    _name = 'custom.popup.mixin'


    def _action_popup(self, title, context={}):
        action = self.env.ref('custom_popup.action_custom_popup_view').read()[0]
        action['name'] = title
        action['context'] = context

        return action