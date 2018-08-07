# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models, osv
from openerp.exceptions import ValidationError
import urlparse, os
import re
import datetime
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp


_ROLES = [
    (1, 'Volunteer'),
    (2, 'Leader')
]

_STUDENTS = [
    (1, 'Student'),
    (2, 'Graduated')
]

class volunteers(models.Model):
    _description = "volunteers"
    _name = 'volunteers'
    #_columns = {
    #    'country_id': fields.many2one('res.country', 'Country', required=True),
    #    'name': fields.char('Gov Name', required=True,
    #                        help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton'),
    #    'code': fields.char('Gov Code', size=3,
    #                        help='The state code in max. three chars.', required=True),
    #    'city_ids': fields.one2many('govs.villages.city', 'city_id', string='Cities'),
    #}
    # journal_id = fields.Many2one('account.journal', string=
    #country_id = fields.Many2one('res.country', 'Country', required=True, default=66)
    #name = fields.Char('Gov Name', required=True)
    #code = fields.Char('Gov Code', size=3, required=True)
    #city_ids = fields.One2many('govs.villages.city', 'gov_id', string='Cities')
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
        
    def _check_value_mobile(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        pattern = "^\+?[0-9]*$"
        for data in record:
            if (data.mobile_phone != False and re.match(pattern, data.mobile_phone) == None):
                return False
        return True
    
    _constraints = [
    (_check_value_mobile, '"You cannot add value other than integer on mobile phone".', ['mobile_phone']),
]
    @api.constrains('mobile_phone2')
    def _check_value_mobile2(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        pattern = "^\+?[0-9]*$"
        for data in record:
            if (data.mobile_phone2 != False and re.match(pattern, data.mobile_phone2) == None):
                raise ValidationError("You cannot add value other than integer on mobile phone2: %s" % record.mobile_phone2)
                return False
        return True
    @api.constrains('national_number')
    def _check_value_national(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        pattern = "^\+?[0-9]*$"
        for data in record:
            if (data.national_number != False and re.match(pattern, data.national_number) == None):
                raise ValidationError("You cannot add value other than integer on national number: %s" % record.national_number)
                return False
        return True
    
    # (_check_value_mobile2, '"You cannot add value other than integer on mobile phone2".', ['mobile_phone2']),
    #(_check_value_national, '"You cannot add value other than integer on national number".', ['national_number'])
    
    name = fields.Char('Volunteer Name', required=True)
    national_number = fields.Char('National Number', required=True, size=14, on_change='_check_value_national')
    mobile_phone = fields.Char('Phone 1', required=True, size=13, on_change='_check_value_mobile')
    mobile_phone2 = fields.Char('Phone 2', required=False, size=13, on_change='_check_value_mobile2')
    country_id = fields.Many2one('res.country', 'Country', required=True, default=66)
    gov_id = fields.Many2one('govs.villages.gov', 'Gov', required=True, on_change="onchange_gov(gov_id)")
    city_id = fields.Many2one('govs.villages.city', 'City', required=True, on_change="onchange_city(city_id)")
    village_id = fields.Many2one('govs.villages.village', 'Village', reqired=False)
    role = fields.Selection(selection=_ROLES, default=1, string='Role')
    student = fields.Selection(selection=_STUDENTS, string='Student/Graduate')
    faculty = fields.Char('Faculty', required=False)
    qualification = fields.Char('Qualification', required=False)
    job = fields.Char('Job', required=False)
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")
    user_id = fields.Many2one('res.users', 'Related user', track_visibility='onchange')
    _order = 'name'
    
    
    def change_colore_on_kanban(self):   
        for record in self:
            color = 0