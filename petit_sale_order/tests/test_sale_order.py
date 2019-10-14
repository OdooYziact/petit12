from .test_common import TestCommon

class TestSaleOrder(TestCommon):
    def setUp(self):
        super(TestSaleOrder, self).setUp()

        self.SO = self.create_sale_order({'partner_id': 1, 'state': 'sent', 'client_order_ref': 'TestRef'})
        self.SOD = self.create_sale_order({'partner_id': 1, 'state': 'sale', 'client_order_ref': False})
        self.SOT = self.create_sale_order({'partner_id': 1, 'state': 'sent', 'client_order_ref': False})

    def test_is_sent_no_clientOrderRef_should_no_react(self):
        self.SO.write({'client_order_ref': False})
        self.assertEqual(SO.client_order_ref, False)

        self.SO.write({'partner_id': [(6, 0, 2)]})
        self.assertEqual(SO.client_order_ref, False)


    def test_is_sale_no_clientOrderRef_should_raise_error(self):
        self.assertRaises(ValidationError, self.SOD.write, {'partner_id': [(6, 0, 2)]})

    def test_is_sale_add_clientOrderRef_should_pass(self):
        self.SOD.write({'client_order_ref': 'Test'})
        self.assertEqual(SOD.client_order_ref, 'Test')

    def test_is_sale_delete_clientOrderRef_should_raise_error(self):
        self.assertRaises(ValidationError, self.SOD.write, {'client_order_ref': False})


    def test_is_sent_change_state_without_clientOrderRef_should_raise_error(self):
        self.assertRaises(ValidationError, self.SOT.write, {'status': 'sale'})

    def test_is_sent_change_state_with_change_clientOrderRef_to_false_should_raise_error(self):
        self.SOT.write, {'client_order_ref': 'Test'}
        self.assertEqual(SOT.client_order_ref, 'Test')

        self.assertRaises(ValidationError, self.SOT.write, {'status': 'sale', 'client_order_ref': False})

    def test_is_sent_change_state_with_clientOrderRef_should_pass(self):
        self.SOT.write, {'client_order_ref': 'Test'}
        self.assertEqual(SOT.client_order_ref, 'Test')

        self.SOT.write({'status': 'sale'})
        self.assertEqual(SOT.state, 'sale')
