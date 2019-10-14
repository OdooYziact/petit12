# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    ### ADDING ###
    @api.model
    def _get_domain(self):
        id = self.env.ref('mrp_repair_order.operation_product_category').id
        return [('categ_id', '=', id)]

    product_tmpl_id = fields.Many2one(comodel_name='product.template', domain=_get_domain)
    expertise = fields.Boolean(string="Expertise", default=False)
    no_approval = fields.Boolean('Need an approval', default=False)


    def _prepare_for_sale(self):
        """
        prepare current record for sale order line
        :return: dict
        """
        product_id = self.product_tmpl_id.product_variant_id if self.product_tmpl_id else False
        if product_id:
            desc = "%s\n\n%s" % (product_id.name_get()[0][1], product_id.description_sale if product_id.description_sale else 'n/c')
        else:
            desc = "%s\n%s" % (self.name, self.note)

        vals = {
            'name': self.name,
            'description': desc,
            'product_id': product_id,
            'product_uom_qty':  self.time_cycle_manual if self.time_cycle else self.time_cycle_manual,
            'operation_id': self,
            'cost_hour': self.workcenter_id.costs_hour or 1.0,
        }

        return vals

