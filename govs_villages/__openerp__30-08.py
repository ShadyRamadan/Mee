# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Govs and Villages",
    "author": "Shady Ramadan, FEED Co. "
              "Odoo Community Association (OCA)",
    "version": "9.0.1.0.0",
    "category": "Govs Management",
    #"depends": [
     #   "res.country"
    #],
    "data": [
        #"security/govs_villages.xml",
        #"security/ir.model.access.csv",
        "data/govs_villages_sequence.xml",
        "data/govs_villages_data.xml",
        "views/govs_villages_view.xml",
        "reports/report_govsvillages.xml",
        "views/govs_villages_report.xml",
    ],
    'demo': [
        "demo/govs_villages_demo.xml",
    ],
    "license": 'LGPL-3',
    "installable": True
}
