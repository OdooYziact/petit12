# -*- coding: utf-8 -*-

import base64
import csv
import io
import logging
from datetime import datetime
from itertools import groupby
from pprint import pprint

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_utils, misc, pycompat

_logger = logging.getLogger(__name__)


def round_float(input):
    return float_utils.float_round(input, precision_digits=2, rounding_method='HALF-UP')


class ExportAccountInvoice(models.TransientModel):
    _name = "export.account.invoice"

    def _get_period(self, period='month'):
        now = datetime.now()

        if period == 'month':
            start_date, end_date = (now + relativedelta(day=1)).date(), now.date()
        elif period == 'previous_month':
            start_date, end_date = (now - relativedelta(months=1, day=1)).date(), (now - relativedelta(months=1, day=31)).date()
        else:
            start_date, end_date = (now + relativedelta(day=1)).date(), now.date()

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


    start_date = fields.Date()
    end_date = fields.Date()
    filename = fields.Char(string='Export', size=256, readonly=True)
    value = fields.Binary(readonly=True)
    journal = fields.Selection([('sale', 'Ventes'), ('purchase', 'Achats')], default="sale")
    period = fields.Selection(
        [
            ('month', 'Mois en cours'),
            ('previous_month', 'Mois précédent'),
            ('custom', 'Personnalisé'),
        ], default="custom", required=True)
    is_forced = fields.Boolean(string="Forcer l'export des factures", default=False)
    is_dummy = fields.Boolean(string='Test', default=True)


    @api.onchange('period')
    def _onchange_period(self):
        self.start_date, self.end_date = self._get_period(self.period)

    def action_export(self):
        """
        Create CSV
        :return: CSV
        """
        # credit, debit col index
        index = [5, 6]
        invoice_ids = self._get_invoice_ids()

        if not invoice_ids:
            raise UserError('Aucune facture à exporter')

        lines = self._prepare_vals(invoice_ids)
        lines = self._round_lines(lines, index)
        credit, debit = self._get_sum(lines, index)

        if not self._check(credit, debit):
            _logger.critical("credit / debit account value are not equal")

        self._write_csv(lines)

        if not self.is_dummy:
            res = self.env['account.invoice.export'].create({
                'journal': self.journal,
                'income': credit,
                'outcome': debit,
            })
            invoice_ids.write({'export_id': res.id})

        return self._download(self._get_filename())


    def _get_invoice_ids(self):
        # Errors
        if not self.start_date or not self.end_date or self.start_date > self.end_date:
            raise UserError(_("La date de début doit être inférieure ou égale à la date de fin."))
        if not self.journal:
            raise UserError(_("Vous devez sélectionner un type d'export."))

        invoice_ids = self.env['account.invoice']._export_invoice(self.start_date, self.end_date, self.journal)

        if not self.is_forced:
            invoice_ids = invoice_ids.filtered(lambda rec: not rec.export_id)

        return invoice_ids

    def create_line(self, journal, operation, values):
        line = []
        invoice = values['invoice']
        date_echeance = fields.Datetime.from_string(invoice.date_due).strftime('%d/%m/%Y') if invoice.date_due else ''
        date_facture = fields.Datetime.from_string(invoice.date_invoice).strftime('%d/%m/%Y') if invoice.date_invoice else ''
        libelle = invoice.partner_id.parent_id.name if invoice.partner_id.parent_id and invoice.partner_id.type in ('invoice') and invoice.partner_id else invoice.partner_id.name
        num = invoice.number if invoice.number != False else ''
        ref = invoice.reference if invoice.reference != False else ''

        if journal == "purchase":
            journal_code = 'HA' if invoice.type == 'in_invoice' else 'AVHA'
        else:
            journal_code = 'VT' if invoice.type == 'out_invoice' else 'AVVE'

        # si 0 alors amount au credit
        if not operation:
            line = [journal_code, values['account'].code, date_echeance, ref if journal == "purchase" else num, date_facture, values['amount'], 0.0, libelle]
        # sinon au debit
        else:
            line = [journal_code, values['account'].code, date_echeance, ref if journal == "purchase" else num, date_facture, 0.0, values['amount'], libelle]

        if journal == "purchase":
            line.append(num)

        return line

    def _get_lines(self, lines, operation, invoice, journal):
        invoice_lines = []

        for account, lines in groupby(lines, lambda rec: rec.account_id):
            subtotal_1, subtotal_2 = 0.0, 0.0

            for line in lines:
                # si valeur négative alors on inverse le sens
                if hasattr(line, 'price_subtotal'):
                    if line.price_subtotal < 0:
                        subtotal_2 += abs(line.price_subtotal)
                    else:
                        subtotal_1 += abs(line.price_subtotal)
                else:
                    if line.amount_total < 0:
                        subtotal_2 += abs(line.amount_total)
                    else:
                        subtotal_1 += abs(line.amount_total)


            # si on a trouvé des valeurs négatives...
            if subtotal_2:
                res = self.create_line(journal, not operation, {'amount': subtotal_2, 'invoice': invoice, 'account': account})
                invoice_lines.append(res)

            if not float_utils.float_is_zero(subtotal_1, precision_digits=5):
                res = self.create_line(journal, operation, {'amount': subtotal_1, 'invoice': invoice, 'account': account})
                invoice_lines.append(res)

        return invoice_lines

    def _prepare_vals(self, invoice_ids):
        res = []

        if self.journal == "purchase":
            headers = ['journal', 'compte', 'date_echeance', 'N_facture', 'date_facture',
                       'credit', 'debit', 'libelle', 'N_piece']
        else:
            headers = ['journal', 'compte', 'date_echeance', 'N_piece', 'date_facture',
                       'credit', 'debit', 'libelle', '']

        res.append(headers)

        for invoice in invoice_ids:
            # FALSE: achat + avoir de vente / TRUE: vente + avoir d'achat
            operation = True if invoice.type in ("in_invoice", "out_refund") else False

            # utile pour le format de sortie et l'ordre des colonnes
            journal = "purchase" if invoice.type in ("in_invoice", "in_refund") else "sales"

            invoice_lines = []
            taxes = []

            ### 1: lignes de facture, on groupe par compte
            invoice_lines.extend(self._get_lines(invoice.invoice_line_ids, operation, invoice, journal))

            ### 2: taxes
            # je pense que l'on peut appliquer la même logique que pour les lignes de facture
            # grouper par compte de tva (mais c'est déjà le cas non ?) et inverser le sens de l'écriture si le montant est négatif
            # dans ce cas on peut encore factoriser ce traitement
            taxes.extend(self._get_lines(invoice.tax_line_ids, operation, invoice, journal))

            ### 3: total (client/fournisseur)
            # si on déjà géré le sens de l'écriture avec 'operation', pas besoin d'inversion pour le total
            amount_total = abs(invoice.amount_total)
            total = self.create_line(journal, not operation, {'amount': amount_total, 'invoice': invoice, 'account': invoice.account_id})

            ### 4:
            # on aggrége toutes les lignes de la facture en fonction du journal...
            sublist = [invoice_lines, taxes, [total]] if self.journal == "purchase" else [[total], taxes, invoice_lines]
            list(map(lambda rec: res.extend(rec), sublist))

        return res

    def _round_lines(self, lines, index):
        for line in lines:
            for i in index:
                if not isinstance(line[i], float):
                    continue
                line[i] = float("%.2f" % round_float(line[i]))
        return lines

    def _get_sum(self, lines, index):
        res = []
        for i in index:
            res.append(sum([line[i] for line in lines if isinstance(line[i], float)]))

        return res

    def _check(self, credit, debit):
        return True if float_compare(credit, debit, precision_digits=2) == 0 else False

    def _write_csv(self, lines):

        # Open CSV, and header line
        csvfile = io.BytesIO()
        writer = pycompat.csv_writer(csvfile, delimiter=';')

        for line in lines:
            writer.writerow(line)

        # Download
        fecvalue = csvfile.getvalue()

        self.write({
            'value': base64.encodestring(fecvalue),
            'filename': 'export',
        })

        csvfile.close()

        return True

    def _get_filename(self):
        date = datetime.now()
        return 'export_' + ('HA_' if self.journal == 'purchase' else 'VT_') + date.strftime("%d_%m")

    def _download(self, filename):
        """
        Download action
        :return: action
        """

        return {
            "type": "ir.actions.act_url",
            "url": "web/content/?model=%s&id=%s&filename_field=filename&field=value&download=true&filename=%s.csv" %
                   (self._name, self.id, filename),
            "target": "new",
        }
