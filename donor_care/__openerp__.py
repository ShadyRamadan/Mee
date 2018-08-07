# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Donor Care',
    'version': '1.0',
    'category': 'Donor Care',
    'author': 'Shady Ramadan',
    'description': """
By this module, you can systemize Donor Care Section in Donation module.
    """,
    'website': '',
    'depends': ['donation','base', 'mail'],
    #"depends" : ['base', 'mail'],
    'data': [
        'security/donation_security.xml',
        'views/donation.xml',
        'views/donation_section.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
