# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'


    ### ADDING ###
    def _prepare_for_sale(self):
        """
        prepare workcenter operations for sale order
        :return: list
        """
        res = [x._prepare_for_sale() for x in self.operation_ids]
        return res