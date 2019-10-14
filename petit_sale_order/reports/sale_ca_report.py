# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleCaReport(models.Model):
    _name = "sale.ca.report"
    _description = "Turn Over Statistics On Invoiced Orders"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Référence commande', readonly=True)
    date = fields.Datetime('Date de commande', readonly=True)
    confirmation_date = fields.Datetime('Date de confirmation', readonly=True)
    product_id = fields.Many2one('product.product', 'Article', readonly=True)
    product_uom = fields.Many2one('product.uom', 'Unité de mesure', readonly=True)
    product_uom_qty = fields.Float('Quantité commandée', readonly=True)
    qty_delivered = fields.Float('Qantité livrée', readonly=True)
    qty_to_invoice = fields.Float('Quantité à facturer', readonly=True)
    qty_invoiced = fields.Float('Quantité facturée', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partenaire', readonly=True)
    company_id = fields.Many2one('res.company', 'Société', readonly=True)
    user_id = fields.Many2one('res.users', 'Vendeur', readonly=True)
    price_total = fields.Float('Total', readonly=True)
    price_subtotal = fields.Float('Total HT', readonly=True)
    amt_to_invoice = fields.Float('Montant à facturer', readonly=True)
    amt_invoiced = fields.Float('Montant facturé', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Modèle d\'article', readonly=True)
    categ_id = fields.Many2one('product.category', 'Catégorie d\'article', readonly=True)
    nbr = fields.Integer('# de lignes', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Liste de prix', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Compte analytique', readonly=True)
    team_id = fields.Many2one('crm.team', 'Equipe de vente', readonly=True, oldname='section_id')
    country_id = fields.Many2one('res.country', 'Pays du partenaire', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Entité commerciale', readonly=True)
    state = fields.Selection([
        ('draft', 'Devis'),
        ('sent', 'Devis envoyé'),
        ('sale', 'Bon de commande'),
        ('done', 'Bloqué'),
        ('cancel', 'Annulé'),
        ('repair_confirmed', 'Réparation confirmée'),
        ], string='Etat', readonly=True)
    weight = fields.Float('Poids brut', readonly=True)
    volume = fields.Float('Volume', readonly=True)

    flag = fields.Selection(string="Type de vente",
                            selection=[
                                ('repair', 'REPARATION'),
                                ('quotation', 'NEGOCE'),
                            ], readonly=True)
    invoice_id = fields.Many2one('account.invoice', string="Factures", readonly=True)
    invoice_date = fields.Date('Date de facture', readonly=True)
    margin = fields.Float('Marge', readonly=True)

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
                    sum(l.amt_to_invoice / COALESCE(cr.rate, 1.0)) as amt_to_invoice,
                    sum(l.amt_invoiced / COALESCE(cr.rate, 1.0)) as amt_invoiced,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.confirmation_date as confirmation_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.analytic_account_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume, 
                    s.flag as flag,
                    sum(l.margin) AS margin,
                    ail.invoice_id as invoice_id,
                    (SELECT date_invoice FROM account_invoice WHERE id = invoice_id) as invoice_date
                    
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
                account_invoice_line ail
                join sale_order_line_invoice_rel solir on (ail.id = solir.invoice_line_id)
                join sale_order_line l on (solir.order_line_id = l.id)
                      join sale_order s on (l.order_id=s.id)
                      join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                    left join currency_rate cr on (cr.currency_id = pp.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.name,
                    s.date_order,
                    s.confirmation_date,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    s.analytic_account_id,
                    s.team_id,
                    p.product_tmpl_id,
                    partner.country_id,
                    partner.commercial_partner_id,
                    s.flag,
                    s.fixed_cost_qty,
                    s.fixed_cost_id, 
                    s.id,
                    ail.invoice_id

        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))
