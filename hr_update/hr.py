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


_logger = logging.getLogger(__name__)


class hr_employee(models.Model):
    _description = 'Employee'
    _name = 'hr.employee'
    _inherit = ['hr.employee']
    
    
    @api.onchange('gov_id')
    def onchange_gov(self):
        res = {}
        if self.gov_id:
            res['domain'] = {'city_id': [('gov_id', '=', self.gov_id.id)]}
            return res
        
    @api.onchange('city_id')
    def onchange_city(self):
        res = {}
        if self.city_id:
            res['domain'] = {'village_id': [('city_id', '=', self.city_id.id)]}
            return res

    
    en_name = fields.Char('English Name', required=True)
    ar_name = fields.Char('Arabic Name', required=True)
    country_id = fields.Many2one('res.country', 'Country', required=True, default=66)
    gov_id = fields.Many2one('govs.villages.gov', 'Gov', required=False, on_change="onchange_gov(gov_id)")
    city_id = fields.Many2one('govs.villages.city', 'City', required=False, on_change="onchange_city(city_id)")
    village_id = fields.Many2one('govs.villages.village', 'Village', reqired=False)
    street = fields.Char('Street', required=False)
    address = fields.Text('Address', required=False)
    #gov_en_id = fields.Char()
    gov_en_id = fields.Many2one('govs.villages.enggov',string='Eng Gov',related = "gov_id.gov_en_id")
    #account_id = fields.Many2one('account.account' ,related='donation_place.account_id',store=True,string = 'Account',readonly=True )
    city_en_id = fields.Many2one('govs.villages.engcity',string='Eng City',related = "city_id.city_en_id")
    village_en_id = fields.Many2one('govs.villages.engvillage',string='Eng Village',related = "village_id.village_en_id")
    street_en = fields.Char()
    address_en = fields.Text()
    
class hr_department(models.Model):
    _name = "hr.department"
    _description = "HR Department"
    _inherit = ['mail.thread', 'ir.needaction_mixin','hr.department']
    
    @api.model
    @api.depends('manager_user')
    def _get_default_employee(self):
        
        requested_by = self.manager_user.id
        #self.employee_id = 
        self.env.cr.execute("SELECT count(hr_employee.id) FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(self.manager_user.id))
        res0 = self.env.cr.fetchone()[0]
        if res0 == 1:
            self.env.cr.execute("SELECT hr_employee.id FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(self.manager_user.id))
            res = self.env.cr.fetchone()[0]
            self.manager_id = res
            
    manager_id = fields.Many2one('hr.employee', compute="_get_default_employee")
    manager_user = fields.Many2one('res.users', store=True ,track_visibility='onchange')
