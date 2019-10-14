# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
# import pudb
#
# import logging
# _logger = logging.getLogger(__name__)


class MrpRepairData(models.Model):
    _name = 'mrp.repair.data'

    specification_id = fields.Many2one(comodel_name="mrp.repair.specification", required=True)

    name = fields.Char(related="specification_id.name", string="Name", readonly=True)
    common = fields.Boolean(related="specification_id.common", default=False, string="Common specification", readonly=True)
    required = fields.Boolean(default=False, string="Required", readonly=True)
    field_type = fields.Selection(related="specification_id.field_type", readonly=True)
    unit = fields.Selection(related="specification_id.unit", readonly=True, default="")
    description = fields.Char(related="specification_id.description", readonly=True, string="Label", required=False)

    value = fields.Char(string="Value", required=False)
    value_text = fields.Char(string="Text", required=False)
    value_float = fields.Float(string="Decimal number", required=False)
    value_int = fields.Integer(string="Integer", required=False)
    value_bool = fields.Boolean(string="Bool", required=False)
    # value_list = TODO: ???

    # display_name = fields.Char(string='Name', compute='_compute_display_name')


    @api.multi
    def name_get(self):
        res = []
        for data in self:
            values = [str(item) for item in [data.description, data.value, data.unit] if item]
            res.append((data.id, " ".join(values)))
        return res

    @api.multi
    def check_required(self):
        if any([elem for elem in self.filtered(lambda x: x.required and not x.value)]):
            raise UserError(_('You must fill in the required specifications.'))


    @api.model
    def get_specifications(self, repair_id):
        repair_model = self.env['mrp.repair.model']
        repair_specification = self.env['mrp.repair.specification']
        routing_id = repair_id.routing_id or False

        if routing_id:
            model_id = repair_model.search([('routing_id', '=', routing_id.id)], limit=1)
            return model_id.get_specifications()

        return repair_specification

    @api.model
    def _prepare_vals(self, field, model_name, model_id):
        return {
            'specification_id': field.id,
            'required': field.required,
        }


    @api.model
    def create_specifications(self, model_name, model_id):

        repair_data = self.env['mrp.repair.data']
        repair_model_id = model_id.repair_model_id or False

        if repair_model_id:
            specifications = repair_model_id.get_specifications()

            for field in specifications:
                vals = self._prepare_vals(field, model_name, model_id)
                repair_data |= self.create(vals)


        return repair_data

    # @api.model
    # def create_specifications(self, repair_id):
    #     repair_model = self.env['mrp.repair.model']
    #     repair_data = self.env['mrp.repair.data']
    #     # routing_id = vals.get('routing_id', False)
    #     repair_model_id = repair_id.repair_model_id or False
    #
    #     if repair_model_id:
    #         specifications = repair_model_id.get_specifications()
    #         for field in specifications:
    #             vals = self._prepare_vals(field)
    #             repair_data |= self.create(vals)
    #
    #             # repair_data |= self.create({
    #             #     'repair_order_id': repair_id.id,
    #             #     'specification_id': field.id,
    #             #     'required': field.required,
    #             # })
    #
    #     return repair_data


