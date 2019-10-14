# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _

from odoo.tools.mimetypes import guess_mimetype
import base64


class IrAttachmentType(models.Model):
    _name = 'ir.attachment.type'
    _order = 'sequence'

    name = fields.Char()
    model = fields.Char()
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)


class IrAttachmentTag(models.Model):
    _name = 'ir.attachment.tag'

    name = fields.Char()
    active = fields.Boolean(default=True)

    @api.multi
    def name_get(self):
        return [(rec.id, rec.name) for rec in self]

    @api.multi
    def to_string(self):
        return ", ".join([rec.name for rec in self])


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    res_model_name = fields.Char(compute='_compute_model_name', string="Document", store=True)
    reference = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('doc'),
                            required=True, readonly=True)
    tag_ids = fields.Many2many(comodel_name='ir.attachment.tag', string="Tags")
    type_id = fields.Many2one(comodel_name='ir.attachment.type', string="Type")

    img_attach = fields.Html('Image', compute="_get_img_html")

    @api.onchange('datas_fname')
    def onchange_datas_fname(self):
        if not self.name: self.name = self.datas_fname

    @api.multi
    def _get_img_html(self):
        for record in self:
            record.img_attach = '<img id="allo-test" src="/web/content/%s"/>' % (record.id) if "image" in record.mimetype else False

    # @api.multi
    # def name_get(self):
    #     return ["{x.res_model_name}/{x.name}".format(x=attachment) for attachment in self]

    @api.multi
    @api.depends('res_model')
    def _compute_model_name(self):
        for attachment in self:
            model = self.env['ir.model'].search([('model', '=', attachment.res_model)])
            attachment.res_model_name = model[0].name if model else ''


    @api.model
    def create(self, vals):
        if vals and not vals.get('name', False) and vals.get('datas'):
            vals['name'] = vals.get('datas_fname', _('New'))

        return super(IrAttachment, self).create(vals)




