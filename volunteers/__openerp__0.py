# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "volunteers",
    "author": "Shady Ramadan, LifeMakers "
              "Odoo Community Association (OCA)",
    "version": "9.0.1.0.0",
    "category": "Volunteers Management",
    #"depends": [
     #   "govs.villages"
    #],
    "data": [
        #"security/purchase_request.xml",
        #"security/ir.model.access.csv",
        "data/volunteers_sequence.xml",
        "data/volunteers_data.xml",
        "views/volunteers_view.xml",
        "reports/report_volunteers.xml",
        "views/volunteers_report.xml",
    ],
    'demo': [
        "demo/volunteers_demo.xml",
    ],
    "license": 'LGPL-3',
    "installable": True
}
