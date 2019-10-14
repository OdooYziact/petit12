# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
# import pudb
# import logging
# _logger = logging.getLogger(__name__)




class RepairModel(models.Model):
    _name = 'mrp.repair.model'

    code = fields.Char(string="Code", required=False)
    name = fields.Char(string="Model", required=False)
    active = fields.Boolean(default=True)

    routing_id = fields.Many2one(comodel_name="mrp.routing", string="Routing", required=False)
    product_category_id = fields.Many2one(comodel_name="product.category", string="Products category", required=True)
    product_count = fields.Integer(related="product_category_id.product_count", required=False)

    
    

    @api.multi
    def _compute_bom_ids(self):
        bom = self.env['mrp.bom']
        for model in self:
            if model.routing_id.id:
                bom_ids = bom.search([('routing_id', '=', model.routing_id.id)])
                model.bom_ids = [(6, False, bom_ids.ids)]
                model.bom_count = len(model.bom_ids)

    @api.multi
    def _compute_common_spec(self):
        self.common_specification_ids = self.env['mrp.repair.specification'].search([('common', '=', True)])


    bom_ids = fields.One2many(comodel_name="mrp.bom", compute=_compute_bom_ids, string="Nomenclature(s)", readonly=True)
    bom_count = fields.Integer("Nomenclatures", compute=_compute_bom_ids, required=False, readonly=True)
    specification_ids = fields.Many2many(comodel_name="mrp.repair.specification", string="Specific fields", domain=[('common', '=', False)])
    common_specification_ids = fields.Many2many(compute=_compute_common_spec, comodel_name="mrp.repair.specification", string="Common specifications", readonly=True)

    _sql_constraints = [
        ('code',
        'UNIQUE(code)',
        "The record must be unique."),
    ]


    def get_specifications(self):
        return self.specification_ids | self.common_specification_ids



    def action_view_product(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Produits',
            'res_model': 'product.product',
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            "context":
                {
                    'search_default_categ_id': self.product_category_id.id,
                },
            # 'domain': [('id', 'in', self.bom_ids.ids)],
        }

    def action_view_bom(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nomenclatures',
            'res_model': 'mrp.bom',
            "view_type": 'form',
            "views": [[False, "tree"], [False, "form"]],
            'domain': [('id', 'in', self.bom_ids.ids)],
        }