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
_ORGANIZATION = [
    (1, 'Crowed Fund'),
    (2, 'Governorate'),
    (3, 'NGO'),
    (4, 'INGO'),
    (5, 'International Organization in Egypt'),
    (6, 'International Organization')
]

class DonationSourceFund(models.Model):
    _name = 'donation.sourcefund'
    _description = 'Code attributed for a Donation Source of Fund'
    _rec_name = 'display_name'

    @api.multi
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.code:
                name = u'[%s] %s' % (camp.code, name)
            camp.display_name = name
            
    @api.multi
    @api.depends('organization')
    def _compute_code(self):
        for source in self:
            if source.organization == 1:
                code = '000' 
            camp.display_name = name
            
    @api.model
    @api.depends('organization')
    def _compute_max_code(self):
        for source in self:
            self.env.cr.execute("SELECT count(id) FROM crossovered_budget_lines")
            my_number = self.env.cr.fetchone()[0]
            if my_number > 0:
                self.env.cr.execute("SELECT Max(max_code) FROM crossovered_budget_lines")
                my_first_number = self.env.cr.fetchone()[0]
                if my_first_number > 0 :
                    my_initals = my_first_number
                else:
                    my_initals = 0
            else:
                my_initals = 0
            budget.max_code = int(my_initals) + 1
    
    @api.depends('project_id','max_code')
    def _compute_code(self):
        for budget in self:
            if budget.project_id:
                self.env.cr.execute("SELECT code FROM project_project where id='%s'" %(budget.project_id.id))
                my_code = self.env.cr.fetchone()[0]
            else:
                my_code = 0
            budget.project_code = my_code
            budget_code = 'DEA-' + str(my_code)
            code2 = int(budget.max_code)
            code3 = '%02d' % code2
            code4 = budget_code+ '-' + code3 
            budget.code =  code4
                                
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=32,store=True)
    organization = fields.Selection(selection=_ORGANIZATION, string='Organization')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name',
                               readonly=True, store=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    nota = fields.Text(string='Notes')
    responsible = fields.Many2one('res.users','Responsibility',track_visibility='onchange')
    fundstream_id = fields.Many2one('donation.fundstream', string='Fund Stream',
        track_visibility='onchange', ondelete='restrict')
    
    _sql_constraints = [
            ('display_name_uniq', 'UNIQUE (name)',  'This Fund-stream already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Fund-stream Code already exists')
        ]