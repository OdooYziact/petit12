# -*- coding: utf-8 -*-

from odoo import models, fields, api

ACTION_CLOSE = {'type': 'ir.actions.act_window_close'}

class CustomPopup(models.TransientModel):
    _name = 'custom.popup'


    @api.model
    def default_get(self, fields):
        result = super(CustomPopup, self).default_get(fields)

        result['model'] = result.get('model', self._context.get('active_model'))
        result['res_id'] = result.get('res_id', self._context.get('active_id'))

        return result

    message = fields.Html(required=True, readonly=True)
    action = fields.Char(readonly=True)
    model = fields.Char(readonly=True)
    res_id = fields.Integer(readonly=True)


    def action_close(self):
        return ACTION_CLOSE

    def action_run(self):

        if not all([self.model, self.res_id, self.action]):
            return ACTION_CLOSE

        record = self.env[self.model].browse(self.res_id)

        if not hasattr(record, self.action):
            return ACTION_CLOSE

        context = dict(self._context or {})
        ctx = context.copy()
        # ctx.update({'force_mail': True})

        func = getattr(record.with_context(**ctx), self.action)

        return func()



