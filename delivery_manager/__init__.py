from . import models
# from . import controllers

from odoo import api, SUPERUSER_ID

# def pre_init_hook(cr):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     env['res.partner'].search([('delivery_day', 'like', 'lundi')]).update({'delivery_day': env.ref('base_weekday.day_0').id})
#
#     # weekday_ids = env['base.weekday'].search([]).ids
#     # partner_ids = env['res.partner'].search([('delivery_day', 'not in', weekday_ids), ('delivery_day', '!=', False)])
#     # for partner in partner_ids:
#     #     print(partner.delivery_day)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    env['res.partner'].search(['|', ('delivery_day', 'ilike', 'lundi'), ('delivery_day', 'ilike', 'Mon')]).update({'delivery_day': env.ref('base_weekday.day_0').id})
    env['res.partner'].search(['|', ('delivery_day', 'ilike', 'mardi'), ('delivery_day', 'ilike', 'Tue')]).update({'delivery_day': env.ref('base_weekday.day_1').id})
    env['res.partner'].search(['|', ('delivery_day', 'ilike', 'mercredi'), ('delivery_day', 'ilike', 'Wed')]).update({'delivery_day': env.ref('base_weekday.day_2').id})
    env['res.partner'].search(['|', ('delivery_day', 'ilike', 'jeudi'), ('delivery_day', 'ilike', 'Thu')]).update({'delivery_day': env.ref('base_weekday.day_3').id})
    env['res.partner'].search(['|', '|', ('delivery_day', 'ilike', 'vendredi'), ('delivery_day', 'ilike', 'Vednredi'),('delivery_day', 'ilike', 'Fri')]).update({'delivery_day': env.ref('base_weekday.day_4').id})
    env['res.partner'].search(['|', ('delivery_day', 'ilike', 'samedi'), ('delivery_day', 'ilike', 'Sat')]).update({'delivery_day': env.ref('base_weekday.day_5').id})
    env['res.partner'].search(['|', ('delivery_day', 'ilike', 'non def')]).update({'delivery_day': env.ref('base_weekday.day_undefined').id})

