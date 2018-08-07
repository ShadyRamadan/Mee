# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Users Govs',
    'version': '1.0',
    'category': 'res users',
    'author': 'Shady Ramadan',
    'description': """
By this module, you can choose Governote and village to users in users module.
    """,
    'website': '',
    #'depends': ['res.users'],
    "depends" : ['base', 'mail'],
    'data': [
        'views/res_users_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
