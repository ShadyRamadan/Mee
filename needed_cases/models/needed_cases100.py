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

_STATES = [
    ('research', 'البحث'),
    ('accreditation', 'الاعتماد'),
    ('drugs', 'المخدرات'),
    ('papers', 'اﻷوراق'),
    ('execution', 'التنفيذ'),
    ('follow', 'المتابعة الاقتصادية')
]

_STATESACC = [
    ('gov_search', 'المراجعة'),
    ('gov_accreditation', 'اعتماد المحافظة'),
    ('responsible_accreditation', 'اعتماد مسئول الاعتماد'),
    ('project_accreditation', 'اعتماد مدير المشروع'),
    ('rejected', 'رفض')
]

_STATESPAPER = [
    ('paper_agree', 'المراجعة'),
    ('responsible_paper', 'اعتماد مسئول اﻷوراق'),
    ('project_paper', 'اعتماد مدير المشروع'),
    ('rejected', 'رفض')
]

_STATESECONOMY = [
    ('non_visit', 'بدون تقارير'),
    ('first_visit', 'التقرير اﻷول'),
    ('second_visit', 'التقرير الثاني'),
    ('third_visit', 'التقرير الثالث'),
    ('fourth_visit','التقرير الرابع')
]

_EDUCATION = [
    (1, 'امي'),
    (2, 'شهادة محو اﻷمية'),
    (3, 'مؤهل متوسط'),
    (4, 'مؤهل عالي')
]

_JOB = [
    (1, 'لا يعمل'),
    (2, 'عامل يومية'),
    (3, 'موظف بعقد مؤثت'),
    (4, 'موظف')
]
_PROJECTS = [
    (1, 'تريسيكل'),
    (2, 'أخرى')
]

_HAVE = [
    (1, 'لم يحصل على أي مشروع'),
    (2, 'حاصل على مشروع من صناع الحياة'),
    (3, 'حاصل على مشروع من جهة أخرى')
]

_DEPENDS = [
    (1, 'يعول'),
    (2, 'لا يعول')
]
_MARITALS = [
    (1, 'أعزب'),
    (2, 'متزوج'),
    (3, 'مطلق'),
    (4, 'أرمل')
]

_GENDER = [
    (1, 'ذكر'),
    (2, 'أنثى')
]

_DEPTS = [
    (1, 'لا يوجد ديون'),
    (2, 'مجدول'),
    (3, 'غير مجدول'),
]

_LIVE_FAMILY = [
    (1, 'الزوج'),
    (2, 'الزوجة'),
    (3, 'كليهما'),
]

_HOUSE_OWNERSHIP = [
    (1, 'تمليك'),
    (2, 'إيجار')
]

_HOUSE_TYPE = [
    (1, 'عائلة'),
    (2, 'خاص')
]

_BATHROOM = [
    (1, 'يوجد'),
    (2, 'لا يوجد')
]

_WALLS = [
    (1, 'طوب أحمر'),
    (2, 'طوب نئ'),
    (3, 'بلوك أبيض')
]

_ROOF = [
    (1, 'خرسانة'),
    (2, 'خشب'),
    (3, 'بوص')
]

_EXP_PROJECT = [
    (1, 'نعم'),
    (2, 'لا')
]

_DRUGS = [
    (1, 'نعم'),
    (2, 'لا')
]

_DRUGS2 = [
    (1, 'إيجابي'),
    (2, 'سلبي')
]

_SMOKING = [
    (1, 'نعم'),
    (2, 'لا')
]

_PAYING = [
    (1, 'نعم'),
    (2, 'لا')
]

_DRIVING = [
    (1, 'نعم'),
    (2, 'لا')
]

_ISSUES = [
    (1, 'نعم'),
    (2, 'لا')
]

_PPROJECTS = [
    (1, 'نعم'),
    (2, 'لا')
]

_PROFESSION = [
    (1, 'الصنعة'),
    (2, 'التروسيكل')
]

_MONEY = [
    (1, 'نعم'),
    (2, 'لا')
]

_OPINION = [
    (1, 'معتمد'),
    (2, 'غير معتمد')
]

_ACCEPTENCE = [
    (1, 'مقبول'),
    (2, 'مرفوض'),
	(3,'إستكمال بيانات')
]

_AGREEPAPER = [
    (1, 'قبول'),
    (2, 'رفض')
]

_ACCTYPE = [
    (1, 'عادي'),
    (2, 'إستثنائي')
]

_CRIMINAL = [
    (1, 'ليس لديه أحكام'),
    (2, 'يوجد أحكام')
]

_EDUCTIONAL = [
    (1,'شهادة دبلوم'),
    (2, 'شهادة ثانوية'),
    (3, 'شهادة اعدادية'),
	(4, 'شهادة ابتدائية'),
	(5, 'شهادة محو أمية')
]

_FAMILYEDUCTIONAL = [
    (1,'امي'),
    (2, 'شهادة محو امية'),
    (3, 'في المرحلة الابتدائية'),
    (4, 'شهادة ابتدائية'),
    (5,'في المرحلة الاعدادية'),
    (6, 'شهادة اعدادية'),
    (7,'في مرحلة الدبلوم'),
    (8,'شهادة دبلوم'),
    (9,'في المرحلة الثانوية'),
    (10,'شهادة ثانوية'),
    (11,'في المرحلة الجامعية'),
    (12,'شهادة جامعية')
]

_HOLDING = [
    (1, 'يمتلك أراضي'),
    (2, 'لا يمتلك أراضي')
]

_INSURANCE = [
    (1, 'مؤمن'),
    (2, 'غير مؤمن')
]

_EXECUTION = [
    (1, 'تم'),
    (2, 'لم يتم')
]

_FILETYPE = [
    (1, 'رقم قومي'),
    (2, 'شهادة ميلاد')
]

_PROJECTINCOIME = [
    (1, 'انتاجي'),
    (2, 'خدمي'),
    (3,'استهلاكي')
]

_RELATION = [
    (1, 'زوجة'),
    (2, 'ابن'),
	(3, 'ابنة'),
	(4, 'والد'),
	(5, 'والدة')
]

_ROLE = [
    (1, 'بحث'),
    (2, 'اعتماد'),
	(3,'متابعة')
]

_PROJECTSTATE = [
    (1, 'ممتاز'),
    (2, 'جيد'),
    (3,'سئ')
]
_TROSIKLTYPE = [
    (1, 'عادي'),
    (2, 'معدل')
]
_SAFETY = [
    (1, 'ممتاز'),
    (2, 'جيد'),
    (3,'ضعيف')
]

_BRIDE = [
    (1, 'نعم'),
    (2, 'لا')
]
_CARE=  [
    (1, 'نعم'),
    (2, 'لا')
]
_CARE2=  [
    (1, 'نعم'),
    (2, 'لا')
]
_PAYDEPT=  [
    (1, 'نعم'),
    (2, 'لا')
]

class needed_cases(models.Model):
    _description = 'needed cases'
    _name = 'needed.cases'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
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
        
    #@api.one
    #@api.depends('accepted2')    
    @api.onchange('accepted2')    
    def onchange_accepted(self):
        res={}
        if self.accepted2: 
                res['value'] = {'accepted4': self.accepted2}
                #rec.accepted4 = rec.accepted2
                return res
   
    @api.onchange('city_id')
    def onchange_city(self):
        res = {}
        if self.city_id:
            res['domain'] = {'village_id': [('city_id', '=', self.city_id.id)]}
            return res
        
    def _check_value_mobile(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        #pattern = "^\+?[0-9]*$"
        pattern = "^01[0-2]{1}[0-9]{8}"
       # pattern = "^\01[0-2]{1}[0-9]{8}*$"
        for data in record:
            if (data.mobile_phone != False and re.match(pattern, data.mobile_phone) == None):
                return False
        return True
    
    #_constraints = [
    #(_check_value_mobile, '"You cannot add value other than integer on mobile phone".', ['mobile_phone']),
#]
    
    #@api.constrains('telephone')
    def _check_value_telephone(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        pattern = "^\+?[0-9]*$"
        for data in record:
            if (data.tel_phone != False and re.match(pattern, data.tel_phone) == None):
                raise ValidationError("You cannot add value other than integer on telephone: %s" % record.tel_phone)
                return False
        return True

    #@api.constrains('national_number')
    def _check_value_national(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        #pattern = "^\+?[0-9]*$"
        pattern = "(2|3)[0-9][0-9][0-1][0-9][0-3][0-9](01|02|03|04|11|12|13|14|15|16|17|18|19|21|22|23|24|25|26|27|28|29|31|32|33|34|35|88)\d\d\d\d\d"
        for data in record:
            if (data.national_number != False and re.match(pattern, data.national_number) == None):
                raise ValidationError("You cannot add value other than integer on national number: %s" % record.national_number)
                return False
        return True

    
    #@api.constrains('name')
    #def _check_value_name(self, cr, uid, ids, context=None):
     #   record = self.browse(cr, uid, ids)
        #pattern = "^\+?[0-9]*$"
      #  pattern = "(([\x{0600}-\x{065F}\x{066A}-\x{06EF}\x{06FA}-\x{06FF}]+)\s){3}([\x{0600}-\x{065F}\x{066A}-\x{06EF}\x{06FA}-\x{06FF}]+)"
       # for data in record:
        #    if (data.name != False and re.match(pattern, data.name) == None):
         #       raise ValidationError("You should enter first name, Second Name, Third name and family name : %s" % record.name)
          #      return False
        #return True

    #@api.constrains('number_family')
    def _check_value_family(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        pattern = "^\+?[0-9]*$"
        for data in record:
            if (data.number_family != False and re.match(pattern, data.number_family) == None):
                raise ValidationError("You cannot add value other than integer on number of family: %s" % record.number_family)
                return False
        return True 
   
    #@api.constrains('number_depends')
    def _check_value_depends(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        pattern = "^\+?[0-9]*$"
        for data in record:
            if (data.number_depends != False and re.match(pattern, data.number_depends) == None):
                raise ValidationError("You cannot add value other than integer on number of family: %s" % record.number_depends)
                return False
        return True 
    
    
    #@api.one
    #@api.constrains('image')
    #def _check_filename(self):
     #   if self.image:
      #    if not self.filename87:
       #     raise ValidationError(_("There is no file"))
        #  else:
        # Check the file's extension
         #   tmp = self.filename87.split('.')
          #  ext = tmp[len(tmp)-1]
           # if ext != 'jpg':
            #    raise ValidationError(_("The file must be a JPG file"))
    
    #@api.one
    #@api.constrains('image_ext')
    #def _check_filename(self):
     #   for rec in self:
      #      if rec.image_ext == True:
       #         raise ValidationError(_("The file must be a JPG file"))
            

    _constraints = [
    (_check_value_national, '"You cannot add value other than integer on national number:".', ['national_number']),
    (_check_value_mobile, '"You cannot add value other than integer on mobile phone".', ['mobile_phone']),
    (_check_value_telephone, '"You cannot add value other than integer on telephone".', ['tel_phone']),
    (_check_value_family, '"You cannot add value other than integer on number family".', ['number_family']),
    (_check_value_depends, '"You cannot add value other than integer on number depends".', ['number_depends']),
    #(legacy_doc1_getFilename, '"The file must be a JPG file".'),
]
    
    
    def onchange_depends(self):
        if self.depends == 2:
            self.number_depends = 0
        else:
            self.number_depends = 0
			
	def onchange_is_not_chronic(self):
	    if self.is_not_chronic_disease == True:
		    self.is_virus_C = False
            self.is_cancer = False
            self.is_kidney_fail = False
			
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
        d = relativedelta(d1, d2).years
        #self.number4 = d2
        #self.number5 = datetime.today()
        #self.number6 = d
        self.age = d
        
     
    #@api.multi
    #def _track_subtype(self, init_values):
     #   for rec in self:
      #      if 'state' in init_values and rec.state == 'research':
       #         return 'needed_cases.mt_request_to_research'
        #    elif 'state' in init_values and rec.state == 'accreditation':
         #       return 'needed_cases.mt_request_to_accreditation'
          #  elif 'state' in init_values and rec.state == 'papers':
           #     return 'needed_cases.mt_request_to_papers'
            #elif 'state' in init_values and rec.state == 'drugs':
             #   return 'needed_cases.mt_request_to_drugs'
            #elif 'state' in init_values and rec.state == 'execution':
             #   return 'needed_cases.mt_request_to_execution'
            #elif 'state' in init_values and rec.state == 'follow':
             #   return 'needed_cases.mt_request_to_follow'
        #return super(NeededCases, self)._track_subtype(init_values)
    #def _state(self):
     #   for rec in self:
      #      if rec.state == 'accreditation' and rec.authorized_opinion == 1 :
       #         rec.state = 'papers'
            #elif rec.state == 'accreditation' and rec.authorized_opinion == 1 :
             #   rec.state = 'accreditation'
            #elif rec.state == 'accreditation' and rec.authorized_opinion == 2 :
        #     #   rec.state = 'accreditation'
         #   elif rec.state == 'accreditation' and rec.authorized_opinion == 2 :
          #      rec.state = 'accreditation'
           # elif rec.state == 'research' :
            #    rec.state = 'research'
            #elif rec.state == 'papers' :
             #   rec.state = 'papers'
            #elif rec.state == 'drugs' :
             #   rec.state = 'drugs'    
            #elif rec.state == 'execution' :
             #   rec.state = 'execution'
           # elif rec.state == 'follow' :
            #    rec.state = 'follow'
            #else:
             #  rec.state = 'research'
               
    def attachment_tree_view(self, cr, uid, ids, context):     
        #xx = self.name     
        domain = ['&', ('res_model', '=', 'needed.cases'), ('res_id', 'in', ids)]
        res_id = ids and ids[0] or False
        return {
            #
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
            }
    
    def _get_attached_docs(self):
        #res = {}
        #attachment = self.pool.get('ir.attachment')
        #for id in ids:
           # employee_attachments = attachment.search(cr, uid, [('res_model', '=', 'needed.cases'), ('res_id', '=', id)], count=True)
          #  res[id] = employee_attachments or 0
         #   self.doc_count = employee_attachments or 0
        res = 5
        self.doc_count = res
        if self.show_images == False:
            self.show_images = True
        elif self.show_images == True:
            self.show_images = False
        

    #_columns = {
     #   'doc_count': fields.function(_get_attached_docs, string="Number of documents attached", type='integer')
    #}
    #doc_count = fields.Function(_get_attached_docs, string="Number of documents attached", type='integer')
    doc_count = fields.Char('number',compute='_get_attached_docs')
    show_images = fields.Boolean('show Images')
        #d2 = 
    # (_check_value_mobile2, '"You cannot add value other than integer on mobile phone2".', ['mobile_phone2']),
    #(_check_value_national, '"You cannot add value other than integer on national number".', ['national_number'])
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='research'
                             )
							 
    state_accreditation = fields.Selection(selection=_STATESACC,
                             string='Status Accreditation',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='gov_search'
                             )
    state_paper = fields.Selection(selection=_STATESPAPER,
                             string='Status Paper',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='paper_agree'
                             )
    def _get_default_image(self, cr, uid, context=None):
        image_path = get_module_resource('needed.cases', 'static/src/img','default_img.png')
        return tools.image.resize_image_big(open(image_path, 'rb').read().encode('base64'))
		
	defaults = {
	    'image': _get_default_image
	}	
	
							 
    image = fields.Binary("Photo", attachment=True,store=True,
        help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized photo", attachment=True,store=True,
        help="Medium-sized photo of the employee. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized photo", attachment=True,store=True,
        help="Small-sized photo of the employee. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")
    #compute='_state'
    space = fields.Char(' ',readonly=True)
    name = fields.Char('Case Name', required=True)
    code = fields.Char('كود المستفيد', required=True)
    mobile_phone = fields.Char('Mobile Phone', required=True, size=13, on_change='_check_value_mobile')
    tel_phone = fields.Char('Telephone', required=False, size=13, on_change='_check_value_telephone')
    national_number = fields.Char('National Number', required=True, size=14, on_change='_check_value_national')
    #number1 = fields.Integer('number1', compute='_number1', readonly=True)
    #number2 = fields.Char('number2', compute='_number2', readonly=True)
    #number3 = fields.Char('number3', compute='_number2', readonly=True)
    #number4 = fields.Char('number4', compute='_number2', readonly=True)
    #number5 = fields.Char('number5', compute='_number2', readonly=True)
    #number6 = fields.Char('number6', compute='_number2', readonly=True)
    gender = fields.Selection(selection=_GENDER, string='Gender', compute='_number1', readonly=True, Store=True)
    age = fields.Integer('Age', compute='_number2', readonly=True, Store=True )
    number_family = fields.Char('Number of Family', required=False, on_change='_check_value_family')
    #accepted2 = fields.Char('Accepted', readonly=False, compute='_accepted2')
    research_state = fields.Selection(selection=_ACCEPTENCE, string='accepted2', compute='_research_state', Store=True, default=False )
    accepted2 = fields.Selection(selection=_ACCEPTENCE, string='accepted2', compute='_accepted2',onchange = 'onchange_accepted', Store=True)
    accepted3 = fields.Selection(selection=_ACCEPTENCE, string='accepted3')
    accepted4 = fields.Selection(selection=_ACCEPTENCE, string="accepted4",store=True)
    accepted_type = fields.Selection(selection=_ACCTYPE, string='Acceptence Type', default=1)
    accepted_reason = fields.Text('Exception Reason')
	
    country_id = fields.Many2one('res.country', 'Country', required=True, default=66)
    gov_id = fields.Many2one('govs.villages.gov', 'Gov', required=True, on_change="onchange_gov(gov_id)")
    city_id = fields.Many2one('govs.villages.city', 'City', required=True, on_change="onchange_city(city_id)")
    village_id = fields.Many2one('govs.villages.village', 'Village', reqired=False)
    street = fields.Char('Street', required=False)
    address = fields.Text('Address', required=False)

    education = fields.Selection(selection=_EDUCATION, string='Education')
    job = fields.Selection(selection=_JOB, string='Job')
    job_type = fields.Char('نوع العمل', required=False)

    project_type = fields.Selection(selection=_PROJECTS, string='Project Type')
    project_other = fields.Char('Other', required=False)
    have_project = fields.Selection(selection=_HAVE, string='Have Project', default=1)
    project_association = fields.Char('Association', required=False)

    marital_status = fields.Selection(selection=_MARITALS, string='Marital Status', required=False)
    depends = fields.Selection(selection=_DEPENDS, string='Depends', required=False, on_change='onchange_depends')
    number_depends = fields.Char('Number of Depends', required=False, on_change='_check_value_depends')
    data_drugs = fields.Boolean(string="بيانات المخدرات")
    data_search = fields.Boolean(string="بيانات البحث")
	
    is_disease = fields.Boolean(string="لا يعاني من أي مرض")
    is_back = fields.Boolean(string="مشاكل في الظهر والمفصل")
    is_chronic_disease = fields.Boolean(string="أمراض مزمنة لا تهدد الحياة")
    other_disease = fields.Char('أخرى',required=False)
    is_not_chronic_disease = fields.Boolean(string="لا يعاني من أمراض مزمنة")
    is_virus_C = fields.Boolean(string="فيروس سي")
    is_kidney_fail = fields.Boolean(string="فشل كلوي")
    is_cancer = fields.Boolean(string="سرطان")
    other_chronic_disease = fields.Char('أخرى',required=False)
    is_right = fields.Boolean(string="سليم")
    is_blind = fields.Boolean(string="عمى")
    is_amputation = fields.Boolean(string="بتر")
    is_paralysis = fields.Boolean(string="شلل")
    is_disability = fields.Boolean(string="إعاقة ذهنية")
    is_problem = fields.Boolean(string="مشكلة في اليد أو القدم")
    is_weakness = fields.Boolean(string="ضعف نظر شديد")
    other_disability = fields.Char('أخرى',required=False)
	
    department_rent = fields.Integer('إيجار شقة')
    associations_expenses = fields.Integer('جمعيات')
    device_payments = fields.Integer('أقساط أجهزة')
    water_gas = fields.Integer('مياه وغاز وكهرباء')
    studying_child = fields.Integer('دروس أولاد')
    home_expenses = fields.Integer('مصروف البيت')
    medicine_expenses = fields.Integer('العلاج')
    smoking_expenses = fields.Integer('التدخين')
    monthly_dept = fields.Integer('قسط دين شهري')
    other_expenses = fields.Integer('أخرى')
    total_expenses = fields.Integer('المجموع', compute='_total_expenses')
    
    person_job = fields.Integer('وظيفة')
    person_craft = fields.Integer('حرفة')
    family_job = fields.Integer('وظيفة')
    family_craft = fields.Integer('حرفة')
    family_salary = fields.Integer('معاش / نفقة مطلقات')
    associations_salary = fields.Integer('من جمعيات خيرية')
    relatives_salary = fields.Integer('مساعدات أقارب')
    department_income = fields.Integer('تحصيل إيجار شقة أو محل')
    other_income = fields.Integer('أخرى')
    total_income = fields.Integer('المجموع', compute='_total_income')
    #qualification = fields.Char('Qualification', required=False)
    #job = fields.Char('Job', required=False)
	
    project_income = fields.Boolean(string="لديك مشروع")
    proj_income_type = fields.Selection(selection=_PROJECTINCOIME, string="نوع المشروع")
    proj_income_year = fields.Char('مدة المشروع')
    proj_first_money = fields.Integer('راس المال اللي بدأ المشروع')
    proj_income_month = fields.Integer('الارباح الشهرية')
    proj_current_money = fields.Integer('راس المال الحالي')
    
    depts = fields.Selection(selection=_DEPTS, string='الديون', required=False)
    total_depts = fields.Float('قيمة الديون')
    reason_depts = fields.Char('سبب الديون')
    relation_depts = fields.Char('الصلة بالدائن')
    live_family = fields.Selection(selection=_LIVE_FAMILY, string='Live with Family', required=False)
    
    is_property = fields.Boolean(string="ليس لديه أي أملاك")
    is_earth = fields.Boolean(string="أراضي")
    is_house = fields.Boolean(string="منزل")
    is_motorbike = fields.Boolean(string="موتوسيكل")
    is_caro = fields.Boolean(string="عربة كارو")
    is_shop = fields.Boolean(string="محل / كشك")
    is_farsha = fields.Boolean(string="فرشة في بيت")
    is_cow = fields.Boolean(string="مواشي")
    is_sheep = fields.Boolean(string="أغنام")
    number_sheep = fields.Integer('عدد اﻷغنام')
    total_earth = fields.Float('قيمة اﻷراضي الزراعية')
    total_cow = fields.Float('قيمة المواشي')
    other_property = fields.Char('أخرى')
    father_property = fields.Text('أملاك الوالد')

    house_ownership = fields.Selection(selection=_HOUSE_OWNERSHIP, string='ملكية المنزل', required=False)
    house_type = fields.Selection(selection=_HOUSE_TYPE, string='نوع المنزل', required=False)
    bathroom = fields.Selection(selection=_BATHROOM, string='يوجد حمام', required=False)
    number_room = fields.Integer('عدد الغرف')
    walls = fields.Selection(selection=_WALLS, string='الحوائط', required=False)
    roof = fields.Selection(selection=_ROOF, string='السقف', required=False)
    
    is_devices = fields.Boolean(string="لا يوجد أجهزة")
    is_television = fields.Boolean(string="تلفزيون")
    is_fridge = fields.Boolean(string="ثلاجة")
    is_cooker = fields.Boolean(string="بوتاجاز")
    is_fans = fields.Boolean(string="مراوح")
    is_washer = fields.Boolean(string="غسالة")
    other_device = fields.Char('أخرى')
    
    experiences_project = fields.Selection(selection=_EXP_PROJECT, string='الخبرة في المشروع', required=False)
    exp_months = fields.Integer('عدد شهور الخبرة')
    
    #volunteering_id = fields.Many2one('volunteers', 'Responsible Volunteers', track_visibility='onchange')
    #volunteer_id = fields.Many2one('volunteers', 'Related Volunteer', track_visibility='onchange')
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the "
                                  "request.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')
    is_active = fields.Boolean(string="Is Active")
    notes = fields.Text('ملاحظات', required=False)
    story = fields.Text('قصة اﻷسرة', required=False)
    criteria = fields.Text('معايير القبول والرفض', required=False)
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")
    user_id = fields.Many2one('res.users', 'Related user', track_visibility='onchange')
    volunteers_ids = fields.One2many('needed.cases.volunteer', 'cases_id',
                               'Volunteers to needed cases',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
    familypaper_ids = fields.One2many('needed.cases.familypaper', 'cases_id',
                               'Family Paper to needed cases',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
    
    economyreports_ids = fields.One2many('needed.cases.economyreports', 'cases_id',
                               'Needed Cases Economy Reports',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
	
    provide_money = fields.Char('اذا كان الفرق بين الدخل والمصروفات اكبر من 500 جنيه من أين يتوفر المبلغ ؟')
    pay_depts = fields.Char('طريقة سداد الدين')
    driving = fields.Selection(selection=_DRIVING, string='بتعرف تسوق', required=False)
    know_project = fields.Char('عرفت عن الجمعية / المشروع ازاي ؟')
    tight_life = fields.Text('بتعمل ايه لما الدنيا تضييق عليك')
    pay_money = fields.Selection(selection=_PAYING, string='هل تقدر تسدد قسط شهري 500 جنية للجمعية ؟')
    drugs = fields.Selection(selection=_DRUGS, string='المخدرات', required=False)
    smoking = fields.Selection(selection=_SMOKING, string='التدخين', required=False)
    previous_issues = fields.Selection(selection=_ISSUES, string='أحكام سابقة', required=False)
    previous_projects =  fields.Selection(selection=_PPROJECTS, string='مشاريع سابقة', required=False)
    what_project = fields.Char('اسم المشروع', required=False)
    trosikle = fields.Text('لو جالك تروسيكل هتعمل بيه ايه ؟', required=False)
    experience_work = fields.Text('هل لديك خبرة في مجال معين او صنعة ؟', required=False)
    profession_trosikle = fields.Selection(selection=_PROFESSION, string='هل تفضل الصنعة أو التروسيكل', required=False)
    static_money = fields.Selection(selection=_MONEY, string='هل تفضل مبلغ شهري ثابت 500 جنية', required=False)
    authorized_opinion = fields.Selection(selection=_OPINION, string='رأي المعتمد', required=False)
    authorized_reason = fields.Text('السبب', required=False)
	
    national_paper = fields.Binary('وجه البطاقة', attachment=True)
    filename = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    national_paper2 = fields.Binary('ظهر البطاقة', attachment=True)
    filename2 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    national_notes = fields.Char('Notes')
    agree_nationalpaper = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد ')
    reason_nationalpaper = fields.Char('سبب رفض المستند')
    agree_nationalpaper2 = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد ')
    reason_nationalpaper2 = fields.Char('سبب رفض المستند')
	
    criminal_case = fields.Binary('الحالة الجنائية', attachment=True)
    filename3 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    criminal_notes = fields.Char('ملاحظات')
    criminal_status = fields.Selection(selection=_CRIMINAL, string='الحالة الجنائية', required=False)
    agree_criminalcase = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_criminalcase = fields.Char('سبب رفض المستند')
	
    eductional_qualification = fields.Binary('المؤهل الدراسي', attachment=True)
    filename4 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    eductional_notes = fields.Char('ملاحظاات')
    qualification = fields.Selection(selection=_EDUCTIONAL, string='المؤهل', required=False)
    agree_eductional = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_eductional = fields.Char('سبب رفض المستند')
	
    social_status = fields.Binary('وجه الحالة الاجتماعية', attachment=True)
    filename6 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    social_status2 = fields.Binary('ظهر الحالة الاجتماعية', attachment=True)
    filename7 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    social_notes = fields.Char('ملاحظات')
    agree_socialstatus = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_socialstatus = fields.Char('سبب رفض المستند')
    agree_socialstatus2 = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_socialstatus2 = fields.Char('سبب رفض المستند')
	
    holding_husband = fields.Binary('الحيازة', attachment=True)
    filename8 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    holding_status = fields.Selection(selection=_INSURANCE, string='حالة الحيازة')
    agree_holdinghusband = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_holdinghusband = fields.Char('سبب رفض المستند')
    
    holding_father = fields.Binary('الحيازة', attachment=True)
    filename24 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    holding_status3 = fields.Selection(selection=_HOLDING, string='حالة الحيازة')
    agree_holdingfather = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_holdingfather = fields.Char('سبب رفض المستند')
	
    holding_wife = fields.Binary('الحيازة', attachment=True)
    filename9 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    holding_status2 = fields.Selection(selection=_HOLDING, string='حالة الحيازة')
    agree_holdingwife = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_holdingwife = fields.Char('سبب رفض المستند')
	
    insurance_husband = fields.Binary('التأمين', attachment=True)
    filename10 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    insurance_status = fields.Selection(selection=_INSURANCE, string='حالة التأمين')
    agree_insuranchusband = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_insurancehusband = fields.Char('سبب رفض المستند')
	
    insurance_wife = fields.Binary('التأمين', attachment=True)
    filename11 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    insurance_status2 = fields.Selection(selection=_INSURANCE, string=' حالة التأمين')
	
    electricty_voucher = fields.Binary('فاتورة الكهرباء', attachment=True)
    filename12 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    electricty_notes = fields.Char('ملاحظات')
	
    water_voucher = fields.Binary('فاتورة المياة', attachment=True)
    filename13 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    water_notes = fields.Char('ملاحظات')
    
    gas_voucher = fields.Binary('فاتورة الغاز', attachment=True)
    filename25 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    gas_notes = fields.Char('ملاحظات')
	
    telephone_voucher = fields.Binary('فاتورة التليفون', attachment=True)
    filename14 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    telephone_notes = fields.Char('ملاحظات')
	
    house_voucher = fields.Binary('ايجار المنزل', attachment=True)
    filename15 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    house_notes = fields.Char('ملاحظات')
	
    drugs_case = fields.Binary('تحليل المخدرات', attachment=True)
    filename16 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    drugs_notes = fields.Char('نوع المخدرات')
    drugs_status = fields.Selection(selection=_DRUGS2, string='تحليل المخدرات', required=False)
	
    date_execution = fields.Date('تاريخ التنفيذ',store=True)
    execution_done = fields.Selection(selection=_EXECUTION, string='التنفيذ', required=False)
	
    contract_agreement = fields.Binary('ورقة 1', attachment=True)
    filename17 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    agree_contract1 = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_contract1 = fields.Char('سبب رفض المستند')
    
    contract_agreement2 = fields.Binary('ورقة 2', attachment=True)
    filename18 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    agree_contract2 = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_contract2 = fields.Char('سبب رفض المستند')
    
    chassih_number = fields.Char('رقم الشاسيه')
    motor_number = fields.Char('رقم الموتور')
    
    recipt = fields.Binary('ايصال استلام', attachment=True)
    filename19 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    agree_recipt = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_recipt = fields.Char('سبب رفض المستند')
    
    decleration = fields.Binary('اقرار', attachment=True)
    filename5 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    decleration_notes = fields.Char('ملاحظات')
    agree_decleration = fields.Selection(selection=_AGREEPAPER, string = 'اعتماد')
    reason_decleration = fields.Char('سبب رفض المستند')
    
    procrastination = fields.Binary('المبايعة', attachment=True)
    filename20 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    authentication = fields.Binary('المصادقة', attachment=True)
    filename21 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    origin_certification = fields.Binary('شهادة المنشأ', attachment=True)
    filename26 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    shassih_detection = fields.Binary('كشف الشاسيه', attachment=True)
    filename27 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    trosikl_invoice = fields.Binary('الفاتورة', attachment=True)
    filename28 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    
    filename87 = fields.Char('file name', readonly = False)
    
    national1 = fields.Binary('وجه البطاقة', attachment=True)
    filename100 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    national1_all = fields.Binary('وجه البطاقة', attachment=True,compute='_compute_images')
    filename100_all = fields.Char('file name',store = False)
    
    national_paper_all = fields.Binary('وجه البطاقة', attachment=True,compute='_compute_images')
    filename_all = fields.Char('file name', readonly = True,store = False)
    national_paper2_all = fields.Binary('ظهر البطاقة', attachment=True,compute='_compute_images')
    filename2_all = fields.Char('file name', readonly = True,store = False)
    
    criminal_case_all = fields.Binary('الحالة الجنائية', attachment=True)
    filename3_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
   
    eductional_qualification_all = fields.Binary('المؤهل الدراسي', attachment=True)
    filename4_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
   
    social_status_all = fields.Binary('وجه الحالة الاجتماعية', attachment=True)
    filename6_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    social_status2_all = fields.Binary('ظهر الحالة الاجتماعية', attachment=True)
    filename7_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    holding_husband_all = fields.Binary('الحيازة', attachment=True)
    filename8_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
   
    holding_father_all = fields.Binary('الحيازة', attachment=True)
    filename24_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    holding_wife_all = fields.Binary('الحيازة', attachment=True)
    filename9_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    insurance_husband_all = fields.Binary('التأمين', attachment=True)
    filename10_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
  
    insurance_wife_all = fields.Binary('التأمين', attachment=True)
    filename11_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
   
    electricty_voucher_all = fields.Binary('فاتورة الكهرباء', attachment=True)
    filename12_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    
    water_voucher_all = fields.Binary('فاتورة المياة', attachment=True)
    filename13_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
        
    gas_voucher_all = fields.Binary('فاتورة الغاز', attachment=True)
    filename25_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    telephone_voucher_all = fields.Binary('فاتورة التليفون', attachment=True)
    filename14_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    house_voucher_all = fields.Binary('ايجار المنزل', attachment=True)
    filename15_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    house_notes = fields.Char('ملاحظات')
    
    drugs_case_all = fields.Binary('تحليل المخدرات', attachment=True)
    filename16_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    contract_agreement_all = fields.Binary('ورقة 1', attachment=True)
    filename17_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    contract_agreement2_all = fields.Binary('ورقة 2', attachment=True)
    filename18_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    recipt_all = fields.Binary('ايصال استلام', attachment=True)
    filename19_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    decleration_all = fields.Binary('اقرار', attachment=True)
    filename5_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
   
    procrastination_all = fields.Binary('المبايعة', attachment=True)
    filename20_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    authentication_all = fields.Binary('المصادقة', attachment=True)
    filename21_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    origin_certification_all = fields.Binary('شهادة المنشأ', attachment=True)
    filename26_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    shassih_detection_all = fields.Binary('كشف الشاسيه', attachment=True)
    filename27_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    trosikl_invoice_all = fields.Binary('الفاتورة', attachment=True)
    filename28_all = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    
    selfid = fields.Char(string = 'selfid',compute='_selfid')
    #image_error = fields.Char('Image Error', readonly=True, store = True ,compute='_compute_ext')
    #image_ext = fields.Boolean('Image Correct',compute='_compute_ext')
    #ext_fil = fields.Char('Image ext', readonly=True,compute = '_compute_ext')
    is_paper = fields.Boolean(string="Is Paper ",
                                 compute="_compute_is_paper",
                                 readonly=True)
    #is_reject = fields.Boolean(string="Is Reject ",
     #                            compute="_compute_is_reject",
      #                           readonly=True)
    _order = 'name'
    
    def _compute_is_paper(self):
        for rec in self:
            usr = self.env['res.users'].browse(self.env.uid)
            if usr.has_group('__export__.res_groups_75'):
                rec.is_paper = True
            else:
                rec.is_paper = False
                
                
            
                
    
    
    @api.one
    def _selfid(self):
        self.selfid = self.id
        
    
    def _compute_images(self):
        for rec in self:
            rec.national1_all = rec.national1
            rec.national_paper_all = rec.national_paper
            rec.national_paper2_all = rec.national_paper2
            rec.criminal_case_all = rec.criminal_case
            rec.eductional_qualification_all = rec.eductional_qualification
            rec.social_status_all = rec.social_status
            rec.social_status2_all = rec.social_status2
            rec.holding_husband_all = rec.holding_husband
            rec.holding_father_all = rec.holding_father
            rec.holding_wife_all = rec.holding_wife
            rec.insurance_husband_all = rec.insurance_husband
            rec.electricty_voucher_all = rec.electricty_voucher
            rec.water_voucher_all = rec.water_voucher
            rec.gas_voucher_all = rec.gas_voucher
            rec.telephone_voucher_all = rec.telephone_voucher
            rec.house_voucher_all = rec.house_voucher
            rec.drugs_case_all = rec.drugs_case
            rec.contract_agreement_all = rec.contract_agreement
            rec.contract_agreement2_all = rec.contract_agreement2
            rec.recipt_all = rec.recipt
            rec.decleration_all = rec.decleration
            rec.procrastination_all = rec.procrastination
            rec.authentication_all = rec.authentication
            rec.origin_certification_all = rec.origin_certification
            rec.shassih_detection_all = rec.shassih_detection
            rec.trosikl_invoice_all = rec.trosikl_invoice
            rec.filename_all = rec.filename
            rec.filename2_all = rec.filename2
            rec.filename3_all = rec.filename3
            rec.filename4_all = rec.filename4
            rec.filename5_all = rec.filename5
            rec.filename6_all = rec.filename6
            rec.filename7_all = rec.filename7
            rec.filename8_all = rec.filename8
            rec.filename9_all = rec.filename9
            rec.filename10_all = rec.filename10
            rec.filename11_all = rec.filename11
            rec.filename12_all = rec.filename12
            rec.filename13_all = rec.filename13
            rec.filename14_all = rec.filename14
            rec.filename15_all = rec.filename15
            rec.filename16_all = rec.filename16
            rec.filename17_all = rec.filename17
            rec.filename18_all = rec.filename18
            rec.filename19_all = rec.filename19
            rec.filename20_all = rec.filename20
            rec.filename21_all = rec.filename21
            rec.filename27_all = rec.filename27
            rec.filename28_all = rec.filename28
            rec.filename24_all = rec.filename24
            rec.filename25_all = rec.filename25
            rec.filename26_all = rec.filename26 
    #@api.depends('filename','filename2')        
    #def _compute_ext(self):        
     #   for rec in self:
      #      if (not isinstance(self.filename, bool)) and (not isinstance(self.filename2, bool)) :
       #         tmp = rec.filename.split('.')
        #        ext = tmp[len(tmp)-1]
         #       tmp2 = rec.filename2.split('.')
          #      ext2 = tmp2[len(tmp2)-1]
           #     if ext != 'jpg':
            #        rec.image_error = ' jpg يجب أن يكون مستند وجه البطاقة بامتداد'
             #       rec.image_ext = True
              #  else:
               #     if ext2 != 'jpg':
                #        rec.image_error = ' jpg يجب أن يكون مستند ظهر البطاقة بامتداد'
                 #       rec.image_ext = True
            #else:
             #   if ( isinstance(self.filename, bool)) or ( isinstance(self.filename2, bool)) :
              #      rec.image_error = ' jpg يجب أن يكون مستند البطاقة بامتداد'
               # else :
                #    rec.image_error = ' jpg يجب أن يكون '
            
    #def _inverse_image_medium(self):
     #   for rec in self:
      #      rec.national1 = (tools.image_resize_image_big(rec.national1_all).read().encode('base64'))
    @api.one
    def legacy_doc1_getFilename(self):
        if (not isinstance(self.national_number, bool)) and (len(self.national_number) > 0):
            #if self.image_ext == True:
            self.filename = str(self.national_number) + '_nationalnumber1.jpg'
            #else:
        #else:   self.filename = str(self.code) + '_nationalnumber1.jpg'
            self.filename2 = str(self.national_number) + '_nationalnumber2.jpg'
            self.filename3 = str(self.national_number) + '_criminalcase.jpg'
            self.filename4 = str(self.national_number) + '_educational.jpg'
            self.filename5 = str(self.national_number) + '_decleration.jpg'
            self.filename6 = str(self.national_number) + '_socialstatus1.jpg'
            self.filename7 = str(self.national_number) + '_socialstatus2.jpg'
            self.filename8 = str(self.national_number) + '_holdinghusband.jpg'
            self.filename9 = str(self.national_number) + '_holdingwife.jpg'
            self.filename10 = str(self.national_number) + '_insurancehusbund.jpg'
            self.filename11 = str(self.national_number) + '_insurancewife.jpg'
            self.filename12 = str(self.national_number) + '_electricty.jpg'
            self.filename13 = str(self.national_number) + '_water.jpg'
            self.filename14 = str(self.national_number) + '_telephone.jpg'
            self.filename15 = str(self.national_number) + '_house.jpg'
            self.filename16 = str(self.national_number) + '_drugs.jpg'
            self.filename17 = str(self.national_number) + '_contract1.jpg'
            self.filename18 = str(self.national_number) + '_contract2.jpg'
            self.filename19 = str(self.national_number) + '_recipt.jpg'
            self.filename20 = str(self.national_number) + '_procrastination.jpg'
            self.filename21 = str(self.national_number) + '_authentication.jpg'
            self.filename24 = str(self.national_number) + '_holdingfather.jpg'
            self.filename25 = str(self.national_number) + '_gas.jpg'
            self.filename26 = str(self.national_number) + '_origin.jpg'
            self.filename27 = str(self.national_number) + '_shassih.jpg'
            self.filename28 = str(self.national_number) + '_invoice.jpg'
        else:
            self.filename = 'filename_nationalnumber1.jpg'
            self.filename2 = 'filename_nationalnumber2.jpg'
            self.filename3 = 'filename_criminalcase.jpg'
            self.filename4 = 'filename_educational.jpg'
            self.filename5 = 'filename_decleration.jpg'
            self.filename6 = 'filename_socialstatus1.jpg'
            self.filename7 = 'filename_socialstatus2.jpg'
            self.filename8 = 'filename_holdinghusband.jpg'
            self.filename9 = 'filename_holdingwife.jpg'
            self.filename10 = 'filename_insurancehusbund.jpg'
            self.filename11 = 'filename_insurancewife.jpg'
            self.filename12 = 'filename_electricty.jpg'
            self.filename13 = 'filename_water.jpg'
            self.filename14 = 'filename_telephone.jpg'
            self.filename15 = 'filename_house.jpg'
            self.filename16 = 'filename_drugs.jpg'
            self.filename17 = 'filename_contract1.jpg'
            self.filename18 = 'filename_contract2.jpg'
            self.filename19 = 'filename_recipt.jpg'
            self.filename20 = 'filename_procrastination.jpg'
            self.filename21 = 'filename_authentication.jpg'
            self.filename24 = 'filename_holdingfather.jpg'
            self.filename25 = 'filename_gas.jpg'
            self.filename26 = 'filename_origin.jpg'
            self.filename27 = 'filename_shasih.jpg'
            self.filename28 = 'filename_invoice.jpg'
            
            
    @api.one
    @api.depends('total_expenses', 'total_income','education','project_type','gov_id','job','depends','age','have_project','is_cancer','is_blind','is_amputation','is_virus_C','is_kidney_fail','is_paralysis','is_disability','is_problem','is_weakness','depts','total_depts','is_earth','total_earth','is_cow','total_cow')
    #@api.depends('education', 'project_type', 'gov_id')
    def _research_state(self):
        inability = self.total_expenses - self.total_income 
        Excess = self.total_income - self.total_expenses
        if self.accepted_type == 1:
            if (self.education == 1 and self.project_type == 1 and self.gov_id.id != 2 ) or (self.job == 4) or (self.depends == 2) or (self.age > 55) or (self.age < 18 ) or (self.have_project == 2) or (self.is_virus_C == True) or (self.is_kidney_fail == True) or (self.is_cancer == True)  or (self.is_blind == True) or (self.is_amputation == True) or (self.is_paralysis == True) or (self.is_disability == True) or (self.is_problem == True) or (self.is_weakness == True) or (inability >= 500) or (Excess >= 400 ) or (self.depts == 3 and self.total_depts > 10000) or (self.depts == 2 and self.total_depts > 15000) or (self.is_earth == True and self.total_earth >= 20000) or (self.is_cow == True and self.total_cow >= 20000):
                self.research_state = 2
            elif self.education == 0 or self.project_type == 0 or self.job == 0 or self.depends == 0 or self.have_project == 0 or self.total_expenses == 0 or self.total_income == 0 or self.depts == 0:
                self.research_state = 3
            elif (self.education == 1 and self.project_type == 1 and self.gov_id.id == 2):
                self.research_state = 1
            else:
                self.research_state = 1
                
        elif self.accepted_type == 2:
            if self.accepted3:
                self.research_state = self.accepted3
    
    @api.one
    @api.depends('total_expenses', 'total_income')
    #@api.depends('education', 'project_type', 'gov_id')
    def _accepted2(self):
        inability = self.total_expenses - self.total_income 
        Excess = self.total_income - self.total_expenses
        if self.accepted_type == 1:
            if (self.education == 1 and self.project_type == 1 and self.gov_id.id != 2 ) or (self.job == 4) or (self.depends == 2) or (self.age > 55) or (self.age < 18 ) or (self.have_project == 2) or (self.is_virus_C == True) or (self.is_kidney_fail == True) or (self.is_cancer == True)  or (self.is_blind == True) or (self.is_amputation == True) or (self.is_paralysis == True) or (self.is_disability == True) or (self.is_problem == True) or (self.is_weakness == True) or (inability >= 500) or (Excess >= 400 ) or (self.depts == 3 and self.total_depts > 10000) or (self.depts == 2 and self.total_depts > 15000) or (self.is_earth == True and self.total_earth >= 20000) or (self.is_cow == True and self.total_cow >= 20000):
                self.accepted2 = 2
                #self.accepted4 = 2
                dd = 2
                #if (not isinstance(self.selfid, bool)):
                #if self.selfid == '':
                 #   self.selfid = 0
                #else:
                if isinstance(self.id, models.NewId):
                    self.selfid = 0
                else:   
                    self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))
     
                 #   self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))
            elif self.education == 0 or self.project_type == 0 or self.job == 0 or self.depends == 0 or self.have_project == 0 or self.total_expenses == 0 or self.total_income == 0 or self.depts == 0:
                self.accepted2 = 3
                #self.accepted4 = 3
                dd = 3
                #if (not isinstance(self.selfid, bool)):
                #if self.selfid == '':
                 #   self.selfid = 0
                #else:   
                if isinstance(self.id, models.NewId):
                    self.selfid = 0
                else:   
                    self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))

                 #   self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))
        #if (self.education == 1 and self.project_type == 1 and self.gov_id.id != 2 ) or (self.job == 4) or (self.depends == 2) or (self.age > 55) or (self.age < 18) or (self.have_project == 2) or (self.is_virus_C == True) or (self.is_kidney_fail == True) or (self.is_cancer == True) or (self.is_blind == True) or (self.is_amputation == True) or (self.is_paralysis == True) or (self.is_disability == True) or (self.is_problem == True) or (self.is_weakness == True) or (inability >= 500) or (Excess >= 400 ) or (self.depts == 3 and self.total_depts > 10000) or (self.depts == 2 and self.total_depts > 15000) or (self.is_earth == True and self.total_earth >= 20000) or (self.is_cow == True and self.total_cow >= 20000):
         #   self.accepted2 = 2
            elif (self.education == 1 and self.project_type == 1 and self.gov_id.id == 2):
                self.accepted2 = 1
                #self.accepted4 = 1
                dd = 1
                #if (not isinstance(self.selfid, bool)):
                #if self.selfid == '':
                if isinstance(self.id, models.NewId):
                    self.selfid = 0
                else:   
                    self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))

                 #   self.selfid = 0
                #else:   
                 #   self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))
            else:
                self.accepted2 = 1
                #self.accepted4 = 1
                dd = 1
                #if (not isinstance(self.selfid, bool)):
                #if self.selfid == '':
                if isinstance(self.id, models.NewId):
                    self.selfid = 0
                else:   
                    self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))
        elif self.accepted_type == 2:
            if self.accepted3:
                self.accepted2 = self.accepted3
               # self.accepted4 = self.accepted3
                dd = self.accepted3
                #if (not isinstance(self.selfid, bool)):
                #if self.selfid == '':
                 #   self.selfid = 0
                #else:   
                if isinstance(self.id, models.NewId):
                    self.selfid = 0
                else:   
                    self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))

                 #   self.env.cr.execute("UPDATE needed_cases SET accepted4 = '%s' where id = '%d'" %(dd,self.id))
            #ff =self.accepted3
            #update({'accepted4':self.accepted3})
		    
    @api.one
    @api.depends('person_job','person_craft','family_job','family_craft','family_salary','associations_salary','relatives_salary','department_income','other_income','proj_income_month')
    def _total_income(self):
        self.total_income = self.person_job + self.person_craft + self.family_job + self.family_craft + self.family_salary + self.associations_salary +  self.relatives_salary + self.department_income + self.other_income + self.proj_income_month
    
    @api.one
    @api.depends('department_rent','associations_expenses','device_payments','water_gas','studying_child','home_expenses','monthly_dept','other_expenses','medicine_expenses','smoking_expenses')
    def _total_expenses(self):
        self.total_expenses = self.department_rent + self.associations_expenses + self.device_payments + self.water_gas + self.studying_child + self.home_expenses +  self.monthly_dept + self.other_expenses + self.medicine_expenses + self.smoking_expenses
                                  
    def change_colore_on_kanban(self):   
        for record in self:
            record.color = 0
            
    
    @api.multi
    def button_to_accreditation(self):
        for rec in self:
            if rec.accepted2 == 1:
                rec.state = 'accreditation'
            elif  rec.accepted2 == 2: 
                rec.state = 'research'
            else:
                rec.state = 'research' 
        return True
    
    @api.one
    @api.depends('number_depends')	
    def button_depends(self):
        for rec in self:
            dn = int(rec.number_depends)
            if dn > 0:
                self.env.cr.execute("DELETE FROM needed_cases_familypaper WHERE cases_id = '%s'" %(self.id))
                for x in range(0,dn):
                    self.env.cr.execute("INSERT INTO needed_cases_familypaper (member_id,cases_id) VALUES ('%s','%s')" %(x+1,self.id))
            else :
			    dn = 0
        return True
		
    @api.multi
    def button_to_papers(self):
        for rec in self:
            if rec.drugs_status == 1:
                rec.state = 'drugs'
            elif rec.drugs_status == 2:
                rec.state = 'papers'
            else:
			    rec.state = 'drugs'
        return True
    
    @api.multi
    def button_to_drugs(self):
        for rec in self:
            if rec.state_accreditation == 'project_accreditation':
			    rec.state = 'drugs'
            else:
			    rec.state = 'accreditation'
        return True

    @api.multi
    def button_execution(self):
        for rec in self:
            rec.state = 'execution'
        return True
    
    @api.multi
    def button_follow(self):
        for rec in self:
            if rec.execution_done == 1:
                rec.state = 'follow'
                self.env.cr.execute("DELETE FROM needed_cases_economyreports WHERE cases_id = '%s'" %(self.id))
                for x in range(0,4):
                    self.env.cr.execute("INSERT INTO needed_cases_economyreports (report_number,cases_id,date_execution) VALUES ('%s','%s','%s')" %(x+1,self.id,self.date_execution))
        return True
    
    @api.multi
    def button_research(self):
        for rec in self:
            rec.state = 'research'
        return True
		
    @api.multi
    def button_gov_search(self):
        for rec in self:
            rec.state_accreditation = 'gov_search'
            rec.state = 'accreditation'
        return True
		
    @api.multi
    def button_to_gov_accreditation(self):
        for rec in self:
            if rec.authorized_opinion == 1:
                rec.state_accreditation = 'gov_accreditation'
            elif rec.authorized_opinion == 2:
			    rec.state_accreditation = 'rejected'
            else:
                rec.state_accreditation = 'gov_search'
        return True
	
    @api.multi
    def button_to_responsible_accreditation(self):
        for rec in self:
            rec.state_accreditation = 'responsible_accreditation'
        return True
		
    @api.multi
    def button_to_project_accreditation(self):
        for rec in self:
            rec.state_accreditation = 'project_accreditation'
            rec.state = 'drugs'
        return True
    
    @api.multi
    def button_paper_agree(self):
        for rec in self:
            rec.state_paper = 'paper_agree'
            #rec.state = 'drugs'
        return True
    
    @api.multi
    def button_to_responsible_paper(self):
        for rec in self:
            rec.state_paper = 'responsible_paper'
        return True
        
    @api.multi
    def button_to_project_paper(self):
        for rec in self:
            rec.state_paper = 'project_paper'
            rec.state = 'execution'
        return True
    
    #@api.one
    #@api.depends('state')    
    #@api.onchange('authorized_opinion')
    #def _onchange_opinion(self):
     #   if self.authorized_opinion == 1:
     #       self.state = 'papers'
      #  else:
       #     statess = self.state
        #    self.state = statess
    
class neededcasesvolunteer(models.Model):

    _name = "needed.cases.volunteer"
    _description = "Needed Cases Volunteer"
    #_inherit = ['mail.thread', 'ir.needaction_mixin']

    volunteer_id = fields.Many2one(
        'volunteers', 'Volunteers',
        track_visibility='onchange')
    cases_id = fields.Many2one('needed.cases',
                                 'Needed Cases',
                                 ondelete='cascade', readonly=True, invisible=True)
    phone = fields.Char(related='volunteer_id.mobile_phone', string='الموبيل')
    role = fields.Selection(selection=_ROLE,string='الدور')
    date_start = fields.Date(string='تاريخ بداية المتابعة', readonly=True,default=fields.Date.context_today,
                             store=True)
    date_finish = fields.Date(string='تاريخ انتهاء المتابعة', required=False,
                                track_visibility='onchange')
    is_active = fields.Boolean(string="نشط",
                                 readonly=False)
    
class neededcasesfamilypaper(models.Model):
    
    _name = "needed.cases.familypaper"
    _description = "Needed Cases Family Paper"
    cases_id = fields.Many2one('needed.cases',
                                 'Needed Cases',
                                 ondelete='cascade', readonly=True, invisible=True)
    code2 = fields.Char(related='cases_id.code',
                                  string='Code',
                                  store=True, readonly=True)
    national_number2 = fields.Char(related='cases_id.national_number',
                                  string='National Number',
                                  store=True, readonly=True)
    member_id = fields.Integer('م')
    file_type = fields.Selection(selection=_FILETYPE, string='نوع الملف')
    name2 = fields.Char('الاسم')
    national_number = fields.Char('الرقم القومي',size=14, on_change='_check_value_national')
    relation = fields.Selection(selection=_RELATION,string='صلة القرابة')
    medical_case = fields.Char('الحالة الصحية')
    education_case = fields.Selection(selection=_FAMILYEDUCTIONAL, string='التعليم')
    job_case = fields.Char('الوظيفة')
    face1 = fields.Binary('وجه البطاقة')
    filename22 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    face2 = fields.Binary('ظهر البطاقة')
    filename23 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
	
    def _check_value_national(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        #pattern = "^\+?[0-9]*$"
        pattern = "(2|3)[0-9][0-9][0-1][0-9][0-3][0-9](01|02|03|04|11|12|13|14|15|16|17|18|19|21|22|23|24|25|26|27|28|29|31|32|33|34|35|88)\d\d\d\d\d"
        for data in record:
            if (data.national_number != False and re.match(pattern, data.national_number) == None):
                raise ValidationError("You cannot add value other than integer on Family Paper national number: %s - %s" % record.name2 % record.national_number)
                return False
        return True


    _constraints = [
    (_check_value_national, '"You cannot add value other than integer on national number:".', ['national_number'])
]
    
    @api.one
    @api.depends('national_number2')
    def legacy_doc1_getFilename(self):
        if (not isinstance(self.national_number, bool)) and (not isinstance(self.national_number2, bool)) and (len(self.code2) > 0):
            self.filename22 = str(self.national_number2) +'_' + str(self.national_number) + '_nationalnumber1.jpg'
            self.filename23 = str(self.national_number2) +'_' + str(self.national_number) + '_nationalnumber2.jpg'
        else:
		    self.filename22 = 'filename_nationalnumber1.jpg'
		    self.filename23 = 'filename_nationalnumber2.jpg'
class neededcaseseconomyreports(models.Model):
    _name = "needed.cases.economyreports"
    _description = "Needed Cases Economy Reports"
    cases_id = fields.Many2one('needed.cases',
                                 'Needed Cases',
                                 ondelete='cascade', readonly=True, invisible=True)
    state_economy = fields.Selection(selection=_STATESECONOMY,
                             string='Status Economy',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='non_visit'
                             )
    
    state = fields.Selection(selection=_STATES,
                             related='cases_id.state',
                             string='Status',
                             store=True,
                             default=False)
    name = fields.Char(related='cases_id.name',
                                  string='Case Name',
                                  store=True,default=False)
    code = fields.Char(related='cases_id.code',
                                  string='كود المستفيد',
                                  store=True,default=False)
    mobile_phone = fields.Char(related='cases_id.mobile_phone',
                                  string='Mobile Phone',
                                  store=True,default=False)
    national_number = fields.Char(related='cases_id.national_number',
                                  string='National Number',
                                  store=True,default=False)
    #number1 = fields.Integer('number1', compute='_number1', readonly=True)
    #number2 = fields.Char('number2', compute='_number2', readonly=True)
    #number3 = fields.Char('number3', compute='_number2', readonly=True)
    #number4 = fields.Char('number4', compute='_number2', readonly=True)
    #number5 = fields.Char('number5', compute='_number2', readonly=True)
    #number6 = fields.Char('number6', compute='_number2', readonly=True)
    number_family = fields.Char(related='cases_id.number_family',
                                  string='Number of Family',
                                  store=True,default=False)
    #accepted2 = fields.Char('Accepted', readonly=False, compute='_accepted2')
    #country_id = fields.Many2one('res.country', 'Country', required=True, default=66)
    #gov_id = fields.Many2one('govs.villages.gov', 'Gov', required=True, on_change="onchange_gov(gov_id)")
    #city_id = fields.Many2one('govs.villages.city', 'City', required=True, on_change="onchange_city(city_id)")
    #village_id = fields.Many2one('govs.villages.village', 'Village', reqired=False)
    
    #date_execution2 = fields.Date(related='cases_id.date_execution',
     #                             string='Execution Date',
      #                            store=True,default=False)
    date_execution = fields.Date('تاريخ التنفيذ')
    report_number = fields.Integer('التقرير', readonly=True)
    report_date = fields.Date('تاريخ التقرير',compute='_report_date',store=True,default=False)
    visit_date = fields.Date('تاريخ الزيارة')
    project_income_daily = fields.Float('دخل المشروع يوميا')
    project_income_weekly = fields.Float('دخل المشروع أسبوعيا')
    project_expenses_daily = fields.Float('مصروفات المشروع يوميا')
    project_expenses_weekly = fields.Float('مصروفات المشروع أسبوعيا')
    project_profit = fields.Float('ربح المشروع' ,store=True,compute='_project_profit')
    home_expenses_daily = fields.Float('مصروفات المنزل يوميا')
    home_expenses_weekly = fields.Float('مصروفات المنزل أسبوعيا')
    project_saving = fields.Float('الادخار', store=True,compute='_project_saving')
    project_state = fields.Selection(selection=_PROJECTSTATE, string="حالة المشروع")
    safety_factor = fields.Selection(selection=_SAFETY, string='عامل اﻷمان')
    trosikl_type = fields.Selection(selection=_TROSIKLTYPE, string='نوع التروسيكل')
    update_type = fields.Char('نوع التعديل')
    trosikl_problem = fields.Text('مشكلة في التروسيكل')
    activity_type = fields.Text('نوع النشاط')
    preparing_bride = fields.Selection(selection=_BRIDE,string="تجهيز عروسة")
    patient_care = fields.Selection(selection=_CARE,string="كفالة مريض")
    orphan_care = fields.Selection(selection=_CARE2,string="كفالة يتيم")
    pay_dept= fields.Selection(selection=_PAYDEPT,string="سداد دين")
    original_dept = fields.Float('مبلغ الدين اﻷصلي')
    pay_done = fields.Float('مبلغ الدين اﻷصلي')
    rest_dept = fields.Float('المتبقي')
    reason_dept = fields.Char('سبب الدين')
    
    @api.multi
    def button_first_visit(self):
        for rec in self:
            rec.state_economy = 'first_visit'
        return True
    
    @api.multi
    def button_second_visit(self):
        for rec in self:
            rec.state_economy = 'second_visit'
        return True
    
    @api.multi
    def button_third_visit(self):
        for rec in self:
            rec.state_economy = 'third_visit'
        return True
    
    @api.multi
    def button_fourth_visit(self):
        for rec in self:
            rec.state_economy = 'fourth_visit'
        return True
        
    
    
    @api.one
    @api.depends('report_number','date_execution')
    def _report_date(self):
        if self.report_number == 1 and self.date_execution:
            d1 = datetime.strptime((self.date_execution),'%Y-%m-%d') 
            new_date = d1 + timedelta(days=14)
            self.report_date = new_date
        elif self.report_number == 2 and self.date_execution:
            d1 = datetime.strptime((self.date_execution),'%Y-%m-%d') 
            new_date = d1 + timedelta(days=28)
            self.report_date = new_date
        elif self.report_number == 3 and self.date_execution:
            d1 = datetime.strptime((self.date_execution),'%Y-%m-%d') 
            new_date = d1 + timedelta(days=42)
            self.report_date = new_date
        elif self.report_number == 4 and self.date_execution:
            d1 = datetime.strptime((self.date_execution),'%Y-%m-%d') 
            new_date = d1 + timedelta(days=56)
            self.report_date = new_date