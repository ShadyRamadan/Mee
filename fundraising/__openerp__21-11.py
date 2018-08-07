# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Fundraising Module',
    'version': '1.0',
    'category': 'fundraising',
    'author': 'Shady Ramadan',
    'description': """
By this module, you can manage Fundraising department of NGS Organisation.
    """,
    'website': '',
    #'depends': ['res.users'],
    "depends" : ['mail','donation','hr'],
    'data': [
        'views/fundraising_view.xml',
        'views/donation.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
