# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_is_zero
from openerp.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_validated = fields.Boolean(compute='_compute_is_validated', string='Article validé', store=True)
    validation_human = fields.Boolean(default=False, string='Vérification Manager')

    @api.depends('categ_id', 'standard_price', 'uom_id', 'seller_ids', 'weight', 'taxes_id', 'validation_human')
    @api.multi
    def _compute_is_validated(self):
        for record in self:
            record.is_validated = record._run_check()[0]

    @api.multi
    def action_check(self):
        result, msg = self._run_check()
        if result:
            msg = ["Tout est correct"]
            title = "Succès - Article valide"
        else:
            title = "Erreur - Article invalide"
        return self.display_validate_message(title, msg)


    @api.multi
    def _run_check(self):
        message = []
        for product in self:
            if product.active:

                if not product.validation_human:
                    err = "ATTENTION : l'article \" %s \" n'a pas encore été contrôlé par un manager." % product.name
                    message.append(err)

                if not product.categ_id:
                    err = "Article \" %s \" => la catégorie n'est pas renseignée." % product.name
                    message.append(err)

                if float_is_zero(product.standard_price, precision_rounding=0.001):
                    err = "Article \" %s \" => le coût n'est pas renseigné." % product.name
                    message.append(err)

                if not product.uom_id:
                    err = "Article \" %s \" => l'unité de mesure n'est pas renseignée." % product.name
                    message.append(err)

                if not product.seller_ids and (not product.bom_ids or 'service' != product.type):
                    err = "Article \" %s \" => pas de fournisseur renseigné." % product.name
                    message.append(err)

                if float_is_zero(product.weight, precision_rounding=0.001) and 'service' != product.type:
                    err = "Article \" %s \" => le poids n'est pas renseigné." % product.name
                    message.append(err)

                if not product.taxes_id:
                    err = "Article \" %s \" => la TVA n'est pas renseignée." % product.name
                    message.append(err)

        res = False if message else True
        return res, message

    def display_validate_message(self, title, message):
        """
        Pop a user message, different than UserError/Warn, do not rollback
        :return: Action to pop wiz' form with "All is ok" or a list with what's wrong
        """

        body = "\n\r".join(message)

        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'src_model': 'product.template',
            'res_model': 'product.wizard.popup',
            'view_mode': 'form',
            'views_id': {'ref': "custom_product_checker.popup_result_product_checker"},
            'context': {'message': body},
            'target': 'new',
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_validated = fields.Boolean(compute='_compute_is_validated', string='Article validé', store=True)
    validation_human = fields.Boolean(default=False, string='Vérification Manager')

    @api.depends('categ_id', 'standard_price', 'uom_id', 'seller_ids', 'weight', 'taxes_id', 'validation_human')
    @api.multi
    def _compute_is_validated(self):
        for record in self:
            record.is_validated = record._run_check()[0]

    @api.multi
    def action_check(self):
        result, msg = self._run_check()
        if result:
            msg = ["Tout est correct"]
            title = "Succès - Article valide"
        else:
            title = "Erreur - Article invalide"
        return self.display_validate_message(title, msg)


    @api.multi
    def _run_check(self):
        message = []
        for product in self:
            if product.active:

                if not product.validation_human:
                    err = "ATTENTION : l'article \" %s \" n'a pas encore été contrôlé par un manager." % product.name
                    message.append(err)

                if not product.categ_id:
                    err = "Article \" %s \" => la catégorie n'est pas renseignée." % product.name
                    message.append(err)

                if float_is_zero(product.standard_price, precision_rounding=0.001):
                    err = "Article \" %s \" => le coût n'est pas renseigné." % product.name
                    message.append(err)

                if not product.uom_id:
                    err = "Article \" %s \" => l'unité de mesure n'est pas renseignée." % product.name
                    message.append(err)

                if not product.seller_ids and (not product.bom_ids or 'service' != product.type):
                    err = "Article \" %s \" => pas de fournisseur renseigné." % product.name
                    message.append(err)

                if float_is_zero(product.weight, precision_rounding=0.001) and 'service' != product.type:
                    err = "Article \" %s \" => le poids n'est pas renseigné." % product.name
                    message.append(err)

                if not product.taxes_id:
                    err = "Article \" %s \" => la TVA n'est pas renseignée." % product.name
                    message.append(err)

        res = False if message else True
        return res, message

    def display_validate_message(self, title, message):
        """
        Pop a user message, different than UserError/Warn, do not rollback
        :return: Action to pop wiz' form with "All is ok" or a list with what's wrong
        """

        body = "\n\r".join(message)

        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'src_model': 'product.template',
            'res_model': 'product.wizard.popup',
            'view_mode': 'form',
            'views_id': {'ref': "custom_product_checker.popup_result_product_checker"},
            'context': {'message': body},
            'target': 'new',
        }

