# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    add_route = fields.Boolean(string="Route", default=True)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            add_route = self.env['ir.config_parameter'].sudo().get_param('purchase_workflow.add_route')
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('purchase_workflow.add_route', self.add_route)


    @api.multi
    def action_view_routes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Routes',
            'res_model': 'purchase.order.route',
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            'context': {
                'search_default_is_open': True,
            }
        }