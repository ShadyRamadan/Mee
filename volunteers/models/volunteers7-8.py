#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, osv
from openerp.exceptions import ValidationError
import urlparse, os
import re
import datetime
from datetime import datetime, timedelta
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp


_ROLES = [
    (1, 'مدير المشروع في المحافظة'),
    (2, 'مسئول بحث أسرة'),
    (3, 'مسئول إعتماد'),
    (4, 'مسئول توثيق'),
    (5, 'مسئول متابعة إقتصادية'),
    (6, 'مسئول تدريب'),
    (7, 'IT مسئول'),
    (8, 'مسئول مركز'),
    (9, 'مسئول مشروع في أحد المراكز'),
    (10, 'متطوع في فريق اﻷبحاث'),
    (11, 'متطوع في فريق الإعتماد'),
    (12, 'متطوع في فريق التوثيق'),
    (13, 'متطوع في فريق المتابعة الإقتصادية'),
    (14, 'متطوع في فريق التدريب'),
    (15, 'IT متطوع في فريق')
]

_STUDENTS = [
    (1, 'طالب'),
    (2, 'خريج')
]

_GENDER = [
    (1, 'ذكر'),
    (2, 'أنثى')
]

_QUAL = [
    (1, 'بكالوريوس طب بشري'),
    (2, 'بكالوريوس طب اسنان'),
    (3,'بكالوريوس طب بيطري'),
    (4,'بكالوريوس علاج طبيعي'),
    (5,'بكالوريوس صيدلة'),
    (6,'بكالوريوس هندسة'),
    (7,'بكالوريوس تجارة'),
    (8,'بكالوريوس علوم'),
    (9,'بكالوريوس حاسبات ومعلومات'),
    (10,'ليسانس ألسن'),
    (11,'ليسانس اداب'),
    (12,'ليسانس تربية'),
    (13,'ليسانس حقوق'),
    (14,'اخرى')
]

_FACULTY = [
    (1, 'كلية الطب البشري'),
    (2, 'كلية طب الاسنان'),
    (3,'كلية الطب البيطري'),
    (4,'كلية العلاج الطبيعي'),
    (5,'كلية الصيدلة'),
    (6,'كلية الهندسة'),
    (7,'كلية التجارة'),
    (8,'كلية العلوم'),
    (9,'كلية الحاسبات والمعلومات'),
    (10,'كلية ألسن'),
    (11,'كلية اداب'),
    (12,'كلية التربية'),
    (13,'كلية الحقوق'),
    (14,'اخرى')
]
class volunteers(models.Model):
    _description = "volunteers"
    _name = 'volunteers'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
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
                raise ValidationError("You cannot add value other than integer on mobile phone: %s" % record.mobile_phone)
                return False
        return True
    
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
        #pattern = "^\+?[0-9]*$"
        pattern = "(2|3)[0-9][0-9][0-1][0-9][0-3][0-9](01|02|03|04|11|12|13|14|15|16|17|18|19|21|22|23|24|25|26|27|28|29|31|32|33|34|35|88)\d\d\d\d\d"
        for data in record:
            if (data.national_number != False and re.match(pattern, data.national_number) == None):
                raise ValidationError("You cannot add value other than integer on national number: %s" % record.national_number)
                return False
        return True
    
    _constraints = [
    (_check_value_national, '"You cannot add value other than integer on national number:".', ['national_number']),    
    (_check_value_mobile, '"You cannot add value other than integer on mobile phone".', ['mobile_phone']),
]
    
    @api.one
    def _number1(self):
        my_first_number = self.national_number
        my_initals = ''.join([s[12] for s in my_first_number.split(' ')])
        #self.number1 = my_initals
        if (int(my_initals) % 2) == 0:
            self.gender = 2
        else:
            self.gender = 1 
            
    @api.one        
    def _number2(self):
        my_first_number = self.national_number
        my_initals = ''.join([s[1:5 +2] for s in my_first_number.split(' ')])
        my_initals2 = ''.join([s[0] for s in my_first_number.split(' ')])
        #self.number2 = my_initals
        #self.number3 = my_initals2
        if my_initals2 == '2':
            my_initals3 = '19' + my_initals
        else:
            my_initals3 = '20' + my_initals
        #self.number3 = my_initals3
        d1 = datetime.today() 
        d2 = datetime(year=int(my_initals3[0:4]), month=int(my_initals3[4:6]), day=int(my_initals3[6:8]))
        self.birthday = d2
        d = relativedelta(d1, d2).years
        #self.number4 = d2
        #self.number5 = datetime.today()
        #self.number6 = d
        self.age = d
    # (_check_value_mobile2, '"You cannot add value other than integer on mobile phone2".', ['mobile_phone2']),
    
    #(_check_value_national, '"You cannot add value other than integer on national number".', ['national_number'])
    
    name = fields.Char('اسم المتطوع', required=True)
    national_number = fields.Char('الرقم القومي', required=True, size=14, on_change='_check_value_national')
    mobile_phone = fields.Char('موبيل 1', required=True, size=13, on_change='_check_value_mobile')
    mobile_phone2 = fields.Char('موبيل 2', required=False, size=13, on_change='_check_value_mobile2')
    email = fields.Char('الإيميل', required=False)
    country_id = fields.Many2one('res.country', 'الدولة', required=True, default=66)
    gov_id = fields.Many2one('govs.villages.gov', 'المحافظة', required=True, on_change="onchange_gov(gov_id)")
    city_id = fields.Many2one('govs.villages.city', 'المركز/المدينة', required=True, on_change="onchange_city(city_id)")
    village_id = fields.Many2one('govs.villages.village', 'القرية/المنطقة', reqired=False)
    role = fields.Selection(selection=_ROLES, default=1, string='الدور')
    student = fields.Selection(selection=_STUDENTS, string='طالب/خريج')
    faculty = fields.Selection(selection=_FACULTY, string ='الكلية', required=False)
    qualification = fields.Selection(selection=_QUAL, string ='المؤهل', required=False)
    qual_other = fields.Char('مؤهل أخر')
    faculty_other = fields.Char('كلية أخرى')
    job = fields.Char('الوظيفة', required=False)
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")
    user_id = fields.Many2one('res.users', 'Related user', track_visibility='onchange')
    gender = fields.Selection(selection=_GENDER, string='Gender', compute='_number1', readonly=True, Store=True)
    age = fields.Integer('Age', compute='_number2', readonly=True, Store=True )
    birthday = fields.Date('Birthday', compute='_number2', readonly=True, Store=True )
    _order = 'name'
    
    
    def change_colore_on_kanban(self):   
        for record in self:
            color = 0