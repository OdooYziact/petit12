# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_fixed_cost_id = fields.Many2one(comodel_name='product.product', default_model='sale.order', string='Default product')
    default_fixed_cost_qty = fields.Float(default_model='sale.order', string='Default quantity')

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     params = self.env['ir.config_parameter'].sudo()
    #
    #     res.update(
    #         default_fixed_cost_id=params.get_param('sale.default_fixed_cost_id', default=False),
    #         default_fixed_cost_qty=params.get_param('sale.default_fixed_cost_qty', default=False),
    #     )
    #     return res
    #
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     self.env['ir.config_parameter'].sudo().set_param('sale.default_fixed_cost_id', self.default_fixed_cost_id.id)
    #     self.env['ir.config_parameter'].sudo().set_param('sale.default_fixed_cost_qty', self.default_fixed_cost_qty)