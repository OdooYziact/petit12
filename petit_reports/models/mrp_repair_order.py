# -*- coding: utf-8 -*-

from collections import OrderedDict
import datetime
from itertools import groupby

from odoo import models, fields, api, _

from odoo.addons.yzi_utils.scripts.fields import get_fields_from_recordset



class MrpRepairOrder(models.Model):
    _inherit = "mrp.repair.order"

    current_date = fields.Date(compute="_get_current_date")

    @api.multi
    def _get_current_date(self):
        self.current_date = datetime.datetime.now()

    # Methode generique pour ordonner les references client en 4 colonnes dans le XML
    def get_references_fields(self):
        return get_fields_from_recordset(self.partner_references, 4, ['name', 'value'])


    def get_specifications_fields(self):
        return get_fields_from_recordset(self.specification_ids, 4, ['description', 'value', 'unit'])

    def get_specifications_fields2(self):
        return get_fields_from_recordset(self.specification_ids, 2, ['description', 'value', 'unit'])


    def get_workcenters_for_report(self):
        workorders = self.production_id._prepare_workorders_for_report()

        wc = []

        for workorder in workorders:
            if workorder['state'] == 'done' and workorder['workcenter'] not in wc:
                wc.append(workorder['workcenter'])

        return wc

    def get_types_attachment_for_report(self):
        attachments = self.env['ir.attachment'].search([('res_model', '=', 'mrp.repair.order'),('res_id', '=', self.id), ('mimetype', '=like', 'image/%')])

        types = []

        for attachment in attachments:
            if attachment.type_id not in types:
                types.append(attachment.type_id)

        for qc in self.production_id.check_ids:
            attachments_qc = self.env['ir.attachment'].search([('res_model', '=', 'quality.check'), ('res_id', '=', qc.id), ('mimetype', '=like', 'image/%')])
            for attachment in attachments_qc:
                if attachment.type_id not in types:
                    types.append(attachment.type_id)

        return types

    def get_attachments_for_report(self):
        return self.env['ir.attachment'].search([('res_model', '=', 'mrp.repair.order'),('res_id', '=', self.id), ('mimetype', '=like', 'image/%')])


    def get_attachments(self):
        data = OrderedDict()
        attachment_ids = self.attachment_ids.filtered(lambda x: 'image/' in x.mimetype).sorted(key=lambda r: r.type_id.sequence)
        for type_id, attachments in groupby(attachment_ids, lambda rec: rec.type_id):
            key = type_id.name if type_id else 'undefined'
            data[key] = [record for record in attachments]

        # for record in self.attachment_ids.sorted(key=lambda r: r.type_id.sequence).filtered(lambda x: 'image/' in x.mimetype):
        #     key = record.type_id.name if record.type_id else 'undefined'
        #     data.setdefault(key, [])
        #     data[key].append(record)

        return data