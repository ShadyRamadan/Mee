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
    (1, 'Crowed Funding'),
    (2, 'Government'),
    (3, 'NGO'),
    (4, 'INGO in Egypt'),
    (5, 'INGO Overseas'),
    (6, 'Multi-Lateral Donor'),
    (7, 'Bi-Lateral Donor'),
    (8, 'Individual Fund/Trust'),
    (9, 'CSR-Cooperate'),
    (10, 'Other')
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
                
    @api.one
    @api.depends('organization')
    def _compute_max_code(self):
            if self.organization == 1:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '0' + code2
                #vals['last_code'] = my_number
            elif self.organization == 2:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '1' + code2
                #vals['last_code'] = my_number
            elif self.organization == 3:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '2' + code2
                #vals['last_code'] = my_number
            elif self.organization == 4:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '3' + code2
                #vals['last_code'] = my_number
            elif self.organization == 5:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '4' + code2  
                #vals['last_code'] = my_number
            elif self.organization == 6:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '5' + code2  
                #vals['last_code'] = my_number
            elif self.organization == 7:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '6' + code2
                #vals['last_code'] = my_number
            elif self.organization == 8:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '7' + code2
                #vals['last_code'] = my_number
            elif self.organization == 9:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '8' + code2
                #vals['last_code'] = my_number
            elif self.organization == 10:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(self.organization))
                my_number = self.env.cr.fetchone()[0]
                code = my_number + 1
                code2 = '%03d' % my_number
                code3 = '9' + code2
                #vals['last_code'] = my_number
            else:
                code3 ='0000'
                my_number = 0
                #vals['last_code'] = 0
            self.code = code3
            #return vals
            vals = {'last_code': my_number}
            return vals
        
    @api.depends('organization','max_code')
    def _compute_code(self):
        for source in self:
            code = ''
            if source.organization == 1:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(source.organization))
                my_number = self.env.cr.fetchone()[0]
                if my_number > 0:
                    self.env.cr.execute("SELECT max(max_code2) FROM donation_sourcefund where organization='%s'" %(source.organization))
                    max_code2 = self.env.cr.fetchone()[0]
                    if max_code2 > 0:
                        codee = max_code2 + 1
                        code3 = '%03d' % codee
                        code = '0' + code3
                    else:
                        code = '0001'
                else:
                    code = '0001'
            elif source.organization == 2:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(source.organization))
                my_number = self.env.cr.fetchone()[0]
                if my_number > 0:
                    self.env.cr.execute("SELECT max(max_code2) FROM donation_sourcefund where organization='%s'" %(source.organization))
                    max_code2 = self.env.cr.fetchone()[0]
                    if max_code2 > 0:
                        codee = max_code2 + 1
                        code3 = '%03d' % codee
                        code = '0' + code3
                    else:
                        code = '1001'
                else:
                    code = '1001'
            elif source.organization == 3:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(source.organization))
                my_number = self.env.cr.fetchone()[0]
                if my_number > 0:
                    self.env.cr.execute("SELECT max(max_code2) FROM donation_sourcefund where organization='%s'" %(source.organization))
                    max_code2 = self.env.cr.fetchone()[0]
                    if max_code2 > 0:
                        codee = max_code2 + 1
                        code3 = '%03d' % codee
                        code = '0' + code3
                    else:
                        code = '2001'
                else:
                    code = '2001'
            elif source.organization == 4:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(source.organization))
                my_number = self.env.cr.fetchone()[0]
                if my_number > 0:
                    self.env.cr.execute("SELECT max(max_code2) FROM donation_sourcefund where organization='%s'" %(source.organization))
                    max_code2 = self.env.cr.fetchone()[0]
                    if max_code2 > 0:
                        codee = max_code2 + 1
                        code3 = '%03d' % codee
                        code = '0' + code3
                    else:
                        code = '3001'
                else:
                    code = '3001'
            elif source.organization == 5:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(source.organization))
                my_number = self.env.cr.fetchone()[0]
                if my_number > 0:
                    self.env.cr.execute("SELECT max(max_code2) FROM donation_sourcefund where organization='%s'" %(source.organization))
                    max_code2 = self.env.cr.fetchone()[0]
                    if max_code2 > 0:
                        codee = max_code2 + 1
                        code3 = '%03d' % codee
                        code = '0' + code3
                    else:
                        code = '4001'
                else:
                    code = '4001'
            elif source.organization == 6:
                self.env.cr.execute("SELECT count(id) FROM donation_sourcefund where organization = '%s'" %(source.organization))
                my_number = self.env.cr.fetchone()[0]
                if my_number > 0:
                    self.env.cr.execute("SELECT max(max_code2) FROM donation_sourcefund where organization='%s'" %(source.organization))
                    max_code2 = self.env.cr.fetchone()[0]
                    if max_code2 > 0:
                        codee = max_code2 + 1
                        code3 = '%03d' % codee
                        code = '0' + code3
                    else:
                        code = '5001'
                else:
                    code = '5001'
            else:
                code = '0000'
            source.code = code
            
    def onchange_address_id(self, cr, uid, ids, address, context=None):
        if address:
            address = self.pool.get('res.partner').browse(cr, uid, address, context=context)
            return {'value': {'partner_phone': address.phone, 'mobile_phone': address.mobile, 'work_email': address.email, 'partner_website': address.website}}
        return {'value': {}}
    
    #@api.onchange('organization')
    #def onchange_org_id(self, cr, uid, ids, context=None):
     #   record = self.browse(cr, uid, ids)
      #  if self.organization:
       #     mynumber = 123
        #    return {'value': {'last_code': my_number}}
        #return {'value': {}}
            
    address_id = fields.Many2one('res.partner',string='Focal Person Of Contact')
    partner_phone = fields.Char('Focal Person Phone', readonly=False)
    mobile_phone = fields.Char('Focal Person Mobile', readonly=False)
    work_email =  fields.Char('Focal Person Email', size=240)
    partner_website = fields.Char('Focal Person website', size=240)               
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=32)
    last_code = fields.Char(string='last code')
    organization = fields.Selection(selection=_ORGANIZATION, string='Type')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name',
                               readonly=True, store=True)
    fundstream_id = fields.Many2one(
        'donation.fundstream', string='Fund Stream',
        track_visibility='onchange', ondelete='restrict')
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    nota = fields.Text(string='Notes')
    responsible = fields.Many2one('res.users','Responsibility',track_visibility='onchange')
    total_amount = fields.Float(string='Total',readonly=True)
    _sql_constraints = [
            ('display_name_uniq', 'UNIQUE (name)',  'This Fund-stream already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Fund-stream Code already exists')
        ]
    
    @api.model
    def create(self, vals):
        return super(DonationSourceFund, self).create(vals)
