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
    total_amount = fields.Float(string="Total")
    
    sub_theme = fields.Selection([
        (1, 'Development'),
        (2, 'Humaniterian')], string='Sub Theme', default=1, index=True, track_visibility='onchange')
    
    _sql_constraints = [
            ('display_name_uniq', 'UNIQUE (name)',  'This Fund-stream already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Fund-stream Code already exists')
        ]