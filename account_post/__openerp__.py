# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Account Move unpost',
    'version': '1.0',
    'category': 'account move',
    'author': 'Shady Ramadan',
    'description': """
By this module, you can choose Governote and village to users in users module.
    """,
    'website': '',
    #'depends': ['res.users'],
    "depends" : ['base', 'mail','account',],
    'data': [
        'views/account_move.xml',
        'views/account.xml',
        'views/account_analytic_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
