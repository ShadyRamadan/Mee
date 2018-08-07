#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
from dateutil.relativedelta import relativedelta
from openerp import tools
from openerp import api, models, fields,osv
from openerp.exceptions import ValidationError
import urlparse, os
import re
from openerp.modules.module import get_module_resource
#from openerp.osv import fields, osv
from openerp.tools.translate import _
#from tools.translate import _
import datetime
from datetime import datetime, timedelta

from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp
from openerp.api import onchange

import logging

#from openerp import models, fields, api


class DonationFundstream(models.Model):
    _name = 'donation.fundstream'
    _description = 'Code attributed for a Donation Campaign'
    _inherit = 'donation.fundstream'
    _rec_name = 'display_name'

   
    total_other = fields.Float(string="Total Other Income",compute='_compute_total_other',store=True)
   
    other_line_ids = fields.One2many('income.line', 'fundstream_id', string='Other Source of Fund', copy=True)
   
    #difference = fields.Float(string='Difference',compute='_compute_difference',store=True)
    
    
    @api.multi
    @api.depends('budget_id','total_fund')
    def _compute_difference(self):
        for fund in self:
            difference = fund.budget_id.total_cost - (fund.total_fund + fund.total_other)
            fund.difference = difference
    
    @api.multi
    @api.depends('total_fund','budget_id')
    def _compute_active(self):
        for fund in self:
            if fund.budget_id.total_cost > 0:
                if fund.budget_id.total_cost - fund.difference > 0:
                    fund.fund_active = True
                else:
                    fund.fund_active = False
            else:
                fund.fund_active = True

    @api.multi
    @api.depends('other_line_ids','other_line_ids.amount')
    def _compute_total_other(self):
        for fund in self:
            total_other = 0.0
            for line in fund.other_line_ids:
                #line_total = line.quantity * line.unit_price
                line_total = line.amount
                total_other += line_total
            fund.total_other = total_other