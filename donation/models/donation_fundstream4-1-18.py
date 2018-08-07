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
    _rec_name = 'display_name'

    @api.multi
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.code:
                name = u'[%s] %s' % (camp.code, name)
            camp.display_name = name
            
    @api.one
    @api.depends('is_education','is_health','is_livelihood','is_cash_assistant','is_basic_needs','is_youth_development','sub_theme')
    def _compute_code(self):
        code = ''
        code2 = 0
        code3 = ''
        my_initals = 0
        for fund in self:
            if fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '101'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '102'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '103'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '104'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '105'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '106'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '123'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '124'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '125'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '126'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '134'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '135'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '136'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '145'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '146'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '156'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '1234'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '1235'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '1236'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '1245'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '1246'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '1256'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '1345'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '1346'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '1356'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '1456'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '12345'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '12346'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '12356'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '12456'
            elif fund.is_education == True and fund.is_health == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '13456'
            elif fund.is_education == True and fund.is_health == True and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '123456'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '201'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '203'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '204'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '205'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '206'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '234'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '235'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '236'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '245'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '246'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '256'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '2345'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '2346'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '2356'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '2456'
            elif fund.is_health == True and fund.is_education == False and fund.is_livelihood == True and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '23456'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '301'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '304'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '305'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '306'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '345'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == True and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '346'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '356'
            elif fund.is_livelihood == True and fund.is_health == False and fund.is_education == False and fund.is_cash_assistant == True and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '3456'
            elif fund.is_cash_assistant == True and fund.is_livelihood == False and fund.is_health == False and fund.is_education == False and fund.is_basic_needs == False and fund.is_youth_development == False:
                code = '401'
            elif fund.is_cash_assistant == True and fund.is_livelihood == False and fund.is_health == False and fund.is_education == False and fund.is_basic_needs == True and fund.is_youth_development == False:
                code = '405'
            elif fund.is_cash_assistant == True and fund.is_livelihood == False and fund.is_health == False and fund.is_education == False and fund.is_basic_needs == False and fund.is_youth_development == True:
                code = '406'
            elif fund.is_cash_assistant == True and fund.is_livelihood == False and fund.is_health == False and fund.is_education == False and fund.is_basic_needs == True and fund.is_youth_development == True:
                code = '456'
            elif fund.is_basic_needs == True and fund.is_cash_assistant == False and fund.is_livelihood == False and fund.is_health == False and fund.is_education == False and fund.is_youth_development == False:
                code = '501'
            elif fund.is_basic_needs == True and fund.is_cash_assistant == False and fund.is_livelihood == False and fund.is_health == False and fund.is_education == False and fund.is_youth_development == True:
                code = '506'
            elif fund.is_youth_development == True and fund.is_basic_needs == True and fund.is_cash_assistant == False and fund.is_livelihood == False and fund.is_health == False and fund.is_education == False:
                code = '601'
            else:
                code = '901'
            if fund.sub_theme == 1:
                    code = code +'01'
            elif fund.sub_theme == 2:
                    code = code + '02'
            self.env.cr.execute("SELECT count(id) FROM donation_fundstream")
            my_number = self.env.cr.fetchone()[0]
            if my_number > 0:    
                self.env.cr.execute("SELECT Max(max_code) FROM donation_fundstream")
                my_first_number = self.env.cr.fetchone()[0]
                if my_first_number > 0 :
                    my_initals = my_first_number
                    #self.env.cr.execute("SELECT char_length(code) FROM donation_fundstream where code ='%s'" %(my_first_number))
                    #length_char = self.env.cr.fetchone()[0]
                    #if length_char == 11:
                    #    my_initals = ''.join([s[8:9 +2] for s in my_first_number.split(' ')])
                    #elif length_char == 12:
                     #   my_initals = ''.join([s[9:10 +2] for s in my_first_number.split(' ')])
                    #elif length_char == 13:
                     #   my_initals = ''.join([s[10:11 +2] for s in my_first_number.split(' ')])
                    #elif length_char == 14:
                     #   my_initals = ''.join([s[11:12 +2] for s in my_first_number.split(' ')])
                else:
                    my_initals = 0
            else:
                my_initals = 0
            code2 = int(my_initals) + 1
            fund.max_code = code2
            code3 = '%03d' % code2
            code4 = code + code3 
            fund.code = 'FS-'+ code4
            
    @api.multi
    #@api.depends('donation_line_ids_partner.amount')          
    def _compute_total(self):
        for partner in self:
            for line in partner.line_ids:
                partner.amount_total += line.amount

    code = fields.Char(string='Code', size=32, compute='_compute_code',store=True)
    max_code = fields.Char(string='Max Code', size=32, compute='_compute_code',store=True)
    name = fields.Char(string='Name', required=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name',
                               readonly=True, store=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    analytic_account_id = fields.Many2one('account.analytic.account', 
                                string='Analytic Account',
                                related='project_id.analytic_account_id',
                                ondelete='restrict')
    nota = fields.Text(string='Notes')
    is_education = fields.Boolean(string="Education")
    is_health = fields.Boolean(string="Health")
    is_livelihood = fields.Boolean(string="Livelihood")
    is_cash_assistant = fields.Boolean(string="Cash Assistant")
    is_basic_needs = fields.Boolean(string="Basic Needs")
    is_youth_development = fields.Boolean(string="Youth Development")
    is_development = fields.Boolean(string="Development")
    is_humanitarian = fields.Boolean(string="Humanitarian")
    project_id = fields.Many2one('project.project',string='Project')
    #total_amount = fields.Float(string="Total")
    total_fund = fields.Float(string="Total",compute='_compute_total_fund',store=True)
    #total_other = fields.Float(string="Total Other Income",compute='_compute_total_other',store=True)
    line_ids = fields.One2many('donation.line', 'fundstream_id', string='Source of Fund', copy=True , on_change='_compute_total_fund')
    #other_line_ids = fields.One2many('income.line', 'fundstream_id', string='Other Source of Fund', copy=True)
    budget_id = fields.Many2one('crossovered.budget',string="Budget")
    cost_budget = fields.Float(related='budget_id.total_cost',string="Total Budget",store=True)
    difference = fields.Float(string='Difference',compute='_compute_difference',store=True)
    fund_active = fields.Boolean('Active',store=True)
    donation_count = fields.Integer(compute='_donation_count', string="# of Donations", readonly=True, store=True)
    responsible = fields.Many2one('res.users','Responsibility',track_visibility='onchange')
    
    @api.multi
    @api.depends('budget_id','total_fund')
    def _compute_difference(self):
        for fund in self:
            difference = fund.total_fund - fund.budget_id.total_cost 
            fund.difference = difference
    
    #@api.multi
    #@api.depends('total_fund','budget_id')
    #def _compute_active(self):
     #   for fund in self:
      #      if fund.budget_id.total_cost > 0:
       #         if fund.budget_id.total_cost - fund.total_fund > 0:
        #            fund.fund_active = True
         #       else:
          #          fund.fund_active = False
           # else:
            #    fund.fund_active = True
    
    @api.multi
    @api.depends('line_ids.fundstream_id')
    def _donation_count(self):
        # The current user may not have access rights for donations
        for fund in self:
            try:
                fund.donation_count = len(fund.line_ids)
            except:
                fund.donation_count = 0
    
    @api.multi
    def _compute_total_fund(self):
        for fund in self:
            total = 0.0
            for line in fund.line_ids:
                #line_total = line.quantity * line.unit_price
                line_total = line.amount
                total += line_total
            fund.total_fund = total
            
    #@api.multi
    #@api.depends('other_line_ids','other_line_ids.amount')
    #def _compute_total_other(self):
     #   for fund in self:
      #      total_other = 0.0
       #     for line in fund.other_line_ids:
          #      #line_total = line.quantity * line.unit_price
        #        line_total = line.amount
         #       total_other += line_total
           # fund.total_other = total_other
            
    
    sub_theme = fields.Selection([
        (1, 'Development'),
        (2, 'Humaniterian')], string='Context', default=1, index=True, track_visibility='onchange')
    
    _sql_constraints = [
            ('display_name_uniq', 'UNIQUE (name)',  'This Fund-stream already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Fund-stream Code already exists')
        ]