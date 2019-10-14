from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

from odoo.addons.yzi_utils.scripts.fields import get_fields_from_recordset

class PartnerReferencesMixin(models.AbstractModel):
    """
        Abstract Model to implement partner references use with other documents.
        partner_references is a dynamic one2many field based on _rel_id/_rel_model

    """
    _name = 'partner.references.mixin'

    _rel_model = fields.Char(default=lambda self: self._name)
    _rel_id = fields.Integer()
    res_model_id = fields.Many2one(compute='_compute_res_model_id', comodel_name='ir.model')
    partner_references = fields.One2many(comodel_name='partner.references.data', inverse_name='res_id',
                                         compute='_compute_partner_references', inverse='_inverse_partner_references')
    references = fields.Char(compute='_compute_references')

    @api.depends('_rel_id', '_rel_model')
    @api.multi
    def _compute_partner_references(self):
        env = self.env['partner.references.data']
        for record in self:
            if not record._rel_id: record._rel_id = record.id
            record.partner_references = env.search(['&', ('res_model', '=', record._rel_model), ('res_id', '=', record._rel_id or record.id)], order='sequence')

    @api.multi
    def _inverse_partner_references(self):
        pass

    @api.multi
    def _compute_res_model_id(self):
        # TODO: à supprimer/déplacer dans partner.references.data
        for record in self:
            record.res_model_id = self.env['ir.model'].sudo().search([('model', '=', record._rel_model)], limit=1).id

    @api.multi
    def write(self, vals):
        check_required = self.env.context.get('check_required', True)

        if 'partner_id' in vals:
            for record in self:
                new_partner_id = self.__get_partner_id(vals)

                # if current partner has changed
                if new_partner_id != record.partner_id:
                    # and actual references must be updated / created
                    if any(record.partner_references.mapped('partner_id').filtered(lambda x: x != new_partner_id)) or not record.partner_references:
                        self.env['partner.references.data'].create_references(new_partner_id, record._rel_id, record._rel_model)
                        check_required = False


        res = super(PartnerReferencesMixin, self).write(vals)

        if check_required:
            if any([elem for elem in self.mapped('partner_references').filtered(lambda x: x.required and not x.value)]):
                raise ValidationError(_('Please specify missing partner references.'))

        return res


    @api.model
    def create(self, vals):
        partner_id = self.__get_partner_id(vals)
        if not partner_id:
            raise ValidationError(_('No partner found.'))

        # if not vals.get('_rel_id', False) or not vals.get('_rel_model', False):
        #     vals['partner_references'] = self._prepare_references(partner_id, new=True)
        #     print(vals['partner_references'])

        # modify context to disable check
        new_context = self.env.context.copy()
        new_context.update({'check_required': False})
        self = self.with_context(**new_context)

        res = super(PartnerReferencesMixin, self).create(vals)


        if not vals.get('_rel_id', False) or not vals.get('_rel_model', False):
            # res._rel_id = res.id
            self.env['partner.references.data'].create_references(partner_id, res.id, self._name)

        return res


    @api.model
    def __get_partner_id(self, vals):
        return self.env['res.partner'].browse(vals.get('partner_id'))


    @api.multi
    def action_clear_references(self):
        return self.mapped('partner_references').with_context({'check_required': False}).write({'value': ''})


    @api.multi
    def action_check_references(self):
        for record in self:
            # Current partner has changed, references must be update
            if any(record.partner_references.mapped('partner_id').filtered(lambda x: x != record.partner_id)):
                record.partner_references.create_references(record.partner_id, record._rel_id, record._rel_model)

    @api.multi
    def action_update_references(self):
        # self.action_check_references()
        _logger.warning('action_update_references')
        env = self.env['partner.references.data']
        for record in self:
            if record.partner_id and record._rel_id and record._rel_model:
                record.partner_references.action_update() if record.partner_references else \
                    env.create_references(record.partner_id, record._rel_id, record._rel_model)



    @api.depends('partner_references')
    def _compute_references(self):
        for record in self:
            partner_references = record.partner_references.search(['&', ('res_model', '=', record._rel_model),
                                                                   ('res_id', '=', record._rel_id),
                                                                   ('value', '!=', '')], limit=3)
            # partner_references = record.partner_references.search([('res_id', '=', record.id)], limit=3)
            record.references = ", ".join([x[1] for x in partner_references.name_get()]) if partner_references else ""


    def get_references_fields(self):
        return get_fields_from_recordset(self.partner_references, 4, ['name', 'value'])



class PartnerReferencesData(models.Model):
    _name = "partner.references.data"


    @api.model
    def default_get(self, fields):
        defaults = super(PartnerReferencesData, self).default_get(fields)

        if self.env.context.get('default_res_model'):
            defaults['res_model_id'] = self.env['ir.model'].sudo().search(
                [('model', '=', self.env.context['default_res_model'])], limit=1).id

        return defaults


    res_id = fields.Integer('Related Document ID', index=True, required=True, ondelete='cascade')
    res_model_id = fields.Many2one(
        'ir.model', 'Related Document Model',
        index=True, ondelete='cascade', required=True)
    res_model = fields.Char(
        'Related Document Model',
        index=True, related='res_model_id.model', store=True, readonly=True)
    res_name = fields.Char(
        'Document Name', compute='_compute_res_name', store=True,
        help="Display name of the related document.", readonly=True)

    reference_id = fields.Many2one(comodel_name="partner.references", readonly=False)
    name = fields.Char(related="reference_id.name", readonly=False, store=True, string='Field')
    sequence = fields.Integer(default=100)
    note = fields.Text(related="reference_id.note", readonly=True)
    required = fields.Boolean(related="reference_id.required", readonly=True)
    value = fields.Char()
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string='Partner')


    @api.model
    def create_references(self, partner_id, res_id, res_model):
        references = partner_id.reference_ids
        res = self.search(['&', ('res_id', '=', res_id), ('res_model', '=', res_model)])

        if any(res.filtered(lambda x: x.partner_id != partner_id)) \
                or references.ids not in res.mapped('reference_id').ids \
                or len(res) < len(references):

            res.unlink()

            for ref in references:
                vals = self._prepare_vals(partner_id, ref, res_id, res_model)
                if not self.create(vals):
                    raise ValidationError(_('Error'))
        return True

    @api.multi
    def action_update(self):
        """
        Remove non existing reference / add missing reference (newer) on partner.
        :return: Boolean
        """
        partner_id = self.mapped('partner_id')[0]
        res_id = self.mapped('res_id')[0]
        res_model = self.mapped('res_model')[0]
        reference_ids = partner_id.reference_ids
        records = self.filtered(lambda x: x.reference_id)

        # remove non existing reference on partner
        records.filtered(lambda x: x.reference_id not in reference_ids).unlink()
        records = records.exists()

        # remove non existing reference on partner
        for ref in reference_ids:
            if ref not in records.mapped('reference_id'):
                records |= self.create(self._prepare_vals(partner_id, ref, res_id, res_model))

        records = records.sorted('sequence')

        return True


    @api.multi
    def action_check(self, partner_id, res_id, res_model):
        references = partner_id.reference_ids
        res = self.search(['&', ('res_id', '=', res_id), ('res_model', '=', res_model)])


    def _prepare_vals(self, partner_id, reference_id, res_id, res_model):
        return {
            'partner_id': partner_id.id,
            'reference_id': reference_id.id,
            'res_id': res_id,
            'res_model': res_model,
            'sequence': reference_id.sequence if reference_id.sequence else 100
        }


    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for record in self:
            if record.res_id and record.res_model and self.env.get(str(record.res_model), False):
                record.res_name = self.env[record.res_model].browse(record.res_id).name_get()[0][1]

    @api.multi
    def name_get(self):
        return [(data.id, " ".join([data.name, data.value] if data.value else [data.name])) for data in self]

    @api.model
    def create(self, vals):
        defaults = self.default_get(self._fields.keys())
        defaults.update(vals)

        if not defaults.get('res_model_id', False):
            defaults['res_model_id'] = self.env['ir.model'].sudo().search([('model', '=', defaults.get('res_model'))], limit=1).id

        return super(PartnerReferencesData, self).create(defaults)



