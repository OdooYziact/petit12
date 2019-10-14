# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

class TestCommon(TransactionCase):
    def setUp(self):
        super(TestCommon, self).setUp()

    def create_sale_order(self, values):
        return self.env['sale.order'].create(values)