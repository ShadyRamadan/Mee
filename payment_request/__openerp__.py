# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Request',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 76,
    'summary': 'Payments Details',
    'description': """
Payment Request Management
==========================

This application enables you to manage important aspects of your company's payments and other details such as their amounts, Expenses, budgets...


You can manage:
---------------
* Payment and Expenses : You can define your employee with User and display Payments
* payments Requests
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
        'purchase'
    ],
    'data': [
        'data/payment_request_sequence.xml',
        'views/payment_request_view.xml',
        'security/payment_request.xml'
    ],
    'demo': ['payment_demo.xml'],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
