from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)


class DocumentAttachment(models.AbstractModel):
    _name = 'document.attachment'


    attachment_ids = fields.One2many(comodel_name='ir.attachment', inverse_name='res_id', compute='_compute_attachment', string='Attachment')
    attachment_count = fields.Integer(default=0, string="# Attachments", compute='_compute_attachment')

    @api.model
    def _get_attachment_domain(self):

        if hasattr(self, 'production_id'):
            # check_ids = record.production_id.mapped('check_ids').filtered(lambda x: x.picture)
            # mrp.production > mrp.workorder > quality.check
            check_ids = self.production_id.mapped('workorder_ids').mapped('check_ids').filtered(lambda x: x.picture)

            # (A and B) or ((C and D) and E)
            domain = ['|', '&', ('res_id', '=', self.id), ('res_model', '=', self._name), '&', '&',
                      ('res_field', '=', 'picture'), ('res_model', '=', 'quality.check'),
                      ('res_id', 'in', check_ids.ids)]
        else:
            domain = [('res_id', '=', self.id), ('res_model', '=', self._name)]

        return domain

    @api.multi
    def _compute_attachment(self):
        env = self.env['ir.attachment']
        for record in self:
            domain = record._get_attachment_domain()
            record.attachment_ids = env.search(domain)
            record.attachment_count = len(record.attachment_ids) if record.attachment_ids else 0

    @api.multi
    def action_view_attachment(self):
        # view_id = self.env.ref('document_attachment.view_attachment_kanban').id
        kanban_view = self.env.ref('mail.view_document_file_kanban', False)
        kanban_view = self.env.ref('document_attachment.view_attachment_kanban', False)
        form_view = self.env.ref('document_attachment.view_attachment_form', False)
        tree_view = self.env.ref('document_attachment.view_attachment_tree', False)
        search_view = self.env.ref('document_attachment.search_attachment_kanban', False)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'ir.attachment',
            "view_type": 'form',
            # "view_mode": 'kanban,tree,form',
            "views": [(kanban_view.id, 'kanban'), (tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': self._get_attachment_domain(),
            'view_ids': self.attachment_ids.ids,
            'search_view_id': search_view.id,
            'context': {
                'search_default_is_open': True,
                # 'default_res_id': self.id,
                'create': False,
                # 'search_default_group_by_type_id': 1,
            }
        }