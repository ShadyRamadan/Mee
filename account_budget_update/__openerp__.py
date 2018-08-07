{
    'name': 'Budgets Management',
    'version': '1.1',
    'category': 'Accounting Management',
    'description': """
Use Budgets.
============================================

Usage:
-----------
- Add Budgets at: Accounting > Budgets 

View:
--------
- Accounting > Budgets > Budget

""",
    'author': 'Shady Ramadan',
    'website': '',
    'images': [],
    'depends': ['account','project','payment_request','advance_request'],
    'data': [
        'views/account_budget_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
