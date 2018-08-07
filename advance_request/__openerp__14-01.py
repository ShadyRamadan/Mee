# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Advance Request',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 76,
    'summary': 'Advances Details',
    'description': """
Advance Request Management
==========================

This application enables you to manage important aspects of your company's advances and other details such as their amounts, settlements, budgets...


You can manage:
---------------
* Advances and settlements : You can define your employee with User and display advances
* advance Requests
* advance Settlements
    """,
    'website': 'shady.ramadan@lifemakers.org',
    'images': [
        'images/hr_department.jpeg',
        'images/hr_employee.jpeg',
        'images/hr_job_position.jpeg',
        'static/src/img/default_image.png',
    ],
    'depends': [
        'base_setup',
        'mail',
        'resource',
        'web_kanban',
        'web_tip',
        'govs_villages'
    ],
    'data': [
        'data/advance_request_sequence.xml',
        'data/advance_settlement_sequence.xml',
        'views/advance_request_view.xml',
        'security/advance_request.xml'
    ],
    'demo': ['advance_demo.xml'],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
