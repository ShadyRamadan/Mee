# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Donation',
    'version': '9.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Manage donations',
    'author': 'Barroux Abbey, Akretion, Odoo Community Association (OCA)',
    'website': 'http://www.barroux.org',
    'depends': ['donation_base','govs_villages','account_budget_update'],
    'data': [
        'security/donation_security.xml',
        'views/donation.xml',
        'views/account.xml',
        'views/donation_campaign.xml',
        'views/donation_fundstream.xml',
        'views/donation_place.xml',
        'views/donation_section.xml',
        'views/donation_sourcefund.xml',
        'views/donation_box.xml',
        'views/donation_vmachine.xml',
        'views/donation_instrument.xml',
        'views/account_budget_view.xml',
        'views/users.xml',
        'views/partner.xml',
        'security/ir.model.access.csv',
        'report/donation_report_view.xml',
        'wizard/donation_validate_view.xml',
        'data/donation_sequence.xml'
        ],
    'post_init_hook': 'update_account_journal',
    'demo': ['demo/donation_demo.xml'],
    'installable': True,
}
