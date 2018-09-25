# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Accounting update',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 90,
    'summary': 'Financial Annuals, Periods , ......',
    'description': "",
    'owner': 'Expert soultions',
    'author': 'Expert Solutions BY:Shady Ramadan Hassan',
    'website': 'http://exp-sa.com',
    'depends': ['account'],
    'data': [
        'views/fiscal_year_view.xml',
        'views/account_period_view.xml',
        'views/journal_period_view.xml',
        'views/account_account_view.xml',
        'views/account_period_close_view.xml',
        'views/account_move_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}