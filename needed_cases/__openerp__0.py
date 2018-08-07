# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "needed cases",
    "author": "Shady Ramadan, LifeMakers "
              "Odoo Community Association (OCA)",
    "version": "9.0.1.0.0",
    "category": "Needed Cases Management",
    #"depends": [
     #   "govs.villages"
    #],
    "depends": [
        "volunteers"
    ],
    "data": [
        #"security/purchase_request.xml",
        #"security/ir.model.access.csv",
        "data/needed_cases_sequence.xml",
        "data/needed_cases_data.xml",
        "views/needed_cases_view.xml",
        "reports/report_neededcases.xml",
        "views/needed_cases_report.xml",
    ],
    'demo': [
        "demo/needed_cases_demo.xml",
    ],
    "license": 'LGPL-3',
    "installable": True
}
