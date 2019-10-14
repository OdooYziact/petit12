# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ### OVERWRITE ###
    date_order = fields.Datetime(string="Date de la demande")

    ### ADDS ###
    partner_contact_id = fields.Many2one('res.partner', string='Contact')

    @api.multi
    def print_quotation(self):
        res = self.write({'state': 'sent'})
        return self.env.ref('purchase.report_purchase_quotation').report_action(self)

    @api.multi
    def action_rfq_send(self):
        # _logger.critical('action_rfq_send')
        # self.filtered(lambda rec: rec.state == 'draft').write({'state': 'sent'})
        self.write({'state': 'sent'})
        return super(PurchaseOrder, self).action_rfq_send()

    # @api.multi
    # def action_rfq_send(self):
    #     '''
    #     This function opens a window to compose an email, with the edi purchase template message loaded by default
    #     '''
    #     self.ensure_one()
    #     ir_model_data = self.env['ir.model.data']
    #     try:
    #         if self.env.context.get('send_rfq', False):
    #             template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_jinja')[1]
    #         else:
    #             template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done_jinja')[1]
    #     except ValueError:
    #         template_id = False
    #     _logger.critical(template_id)
    #     try:
    #         compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
    #     except ValueError:
    #         compose_form_id = False
    #     ctx = dict(self.env.context or {})
    #     ctx.update({
    #         'default_model': 'purchase.order',
    #         'default_res_id': self.ids[0],
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_composition_mode': 'comment',
    #         'custom_layout': "purchase.mail_template_data_notification_email_purchase_order",
    #         'purchase_mark_rfq_sent': True,
    #         'force_email': True
    #     })
    #     return {
    #         'name': _('Compose Email'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(compose_form_id, 'form')],
    #         'view_id': compose_form_id,
    #         'target': 'new',
    #         'context': ctx,
    #     }        
        

# class MailComposeMessage(models.TransientModel):
#     _inherit = 'mail.compose.message'

#     @api.multi
#     def mail_purchase_order_on_send(self):
#         _logger.critical(self._context.keys())
#         if self._context.get('purchase_mark_rfq_sent'):
#             order = self.env['purchase.order'].browse(self._context['default_res_id'])
#             order.filtered(lambda rec: rec.state == 'draft').write({'state': 'sent'})
#             _logger.critical("%s, %s" % (order.name, order.state))