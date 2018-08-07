{
    'name': 'Other Income Management',
    'version': '1.0',
    'category': 'Accounting Management',
    'description': """
Use Budgets.
============================================

Usage:
-----------
- Add Incoms at: Accounting > Other Incomes 

View:
--------
- Accounting > Other Incomes > Other Incomes

""",
    'author': 'Shady Ramadan',
    'website': '',
    'images': [],
    'depends': ['account','project','purchase_requisition','donation'],
    'data': [
        'views/other_income_view.xml',
        'views/income_type.xml',
        'views/income_method.xml',
        'views/res_bank_view.xml',
        'views/donation_fundstream.xml'
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}