# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models, osv
from openerp.exceptions import ValidationError
import urlparse, os
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp
from openerp.api import onchange

_STATES = [
    ('research', 'Research'),
    ('accreditation', 'Accreditation'),
    ('papers', 'Papers'),
    ('drugs', 'Drugs'),
    ('execution', 'Execution'),
    ('follow', 'Follow Up')
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
    (3, 'بلوك أبيض'),
]

_ROOF = [
    (1, 'خرسانة'),
    (2, 'خشب'),
    (3, 'بوص'),
]

_EXP_PROJECT = [
    (1, 'نعم'),
    (2, 'لا')
]

_DRUGS = [
    (1, 'نعم'),
    (2, 'لا')
]

_SMOKING = [
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
    (2, 'مرفوض')
]

class needed_cases(models.Model):
    _description = 'needed cases'
    _name = 'needed.cases'
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

    _constraints = [
    (_check_value_national, '"You cannot add value other than integer on national number:".', ['national_number']),
    (_check_value_mobile, '"You cannot add value other than integer on mobile phone".', ['mobile_phone']),
    (_check_value_telephone, '"You cannot add value other than integer on telephone".', ['tel_phone']),
    (_check_value_family, '"You cannot add value other than integer on number family".', ['number_family']),
    (_check_value_depends, '"You cannot add value other than integer on number depends".', ['number_depends']),
]
    
    
    def onchange_depends(self):
        if self.depends == 2:
            self.number_depends = 0
        else:
            self.number_depends = 0
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
    def _state(self):
        for rec in self:
            if rec.state == 'accreditation' and rec.authorized_opinion == 1 :
                rec.state = 'papers'
            #elif rec.state == 'accreditation' and rec.authorized_opinion == 1 :
             #   rec.state = 'accreditation'
            #elif rec.state == 'accreditation' and rec.authorized_opinion == 2 :
             #   rec.state = 'accreditation'
            elif rec.state == 'accreditation' and rec.authorized_opinion == 2 :
                rec.state = 'accreditation'
            elif rec.state == 'research' :
                rec.state = 'research'
            elif rec.state == 'papers' :
                rec.state = 'papers'
            elif rec.state == 'drugs' :
                rec.state = 'drugs'    
            elif rec.state == 'execution' :
                rec.state = 'execution'
            elif rec.state == 'follow' :
                rec.state = 'follow'
            else:
               rec.state = 'research'
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
    #compute='_state'
    name = fields.Char('Case Name', required=True)
    mobile_phone = fields.Char('Mobile Phone', required=True, size=13, on_change='_check_value_mobile')
    tel_phone = fields.Char('Telephone', required=False, size=13, on_change='_check_value_telephone')
    national_number = fields.Char('National Number', required=True, size=14, on_change='_check_value_national')
    #number1 = fields.Integer('number1', compute='_number1', readonly=True)
    #number2 = fields.Char('number2', compute='_number2', readonly=True)
    #number3 = fields.Char('number3', compute='_number2', readonly=True)
    #number4 = fields.Char('number4', compute='_number2', readonly=True)
    #number5 = fields.Char('number5', compute='_number2', readonly=True)
    #number6 = fields.Char('number6', compute='_number2', readonly=True)
    gender = fields.Selection(selection=_GENDER, string='Gender', compute='_number1', readonly=True)
    age = fields.Integer('Age', compute='_number2', readonly=True)
    number_family = fields.Char('Number of Family', required=False, on_change='_check_value_family')
    #accepted2 = fields.Char('Accepted', readonly=False, compute='_accepted2')
    accepted2 = fields.Selection(selection=_ACCEPTENCE, string='State', compute='_accepted2', readonly=True)
    
    country_id = fields.Many2one('res.country', 'Country', required=True, default=66)
    gov_id = fields.Many2one('govs.villages.gov', 'Gov', required=True, on_change="onchange_gov(gov_id)")
    city_id = fields.Many2one('govs.villages.city', 'City', required=True, on_change="onchange_city(city_id)")
    village_id = fields.Many2one('govs.villages.village', 'Village', reqired=False)
    street = fields.Char('Street', required=False)
    address = fields.Text('Address', required=False)

    education = fields.Selection(selection=_EDUCATION, string='Education')
    job = fields.Selection(selection=_JOB, string='Job')

    project_type = fields.Selection(selection=_PROJECTS, string='Project Type')
    project_other = fields.Char('Other', required=False)
    have_project = fields.Selection(selection=_HAVE, string='Have Project', default=1)
    project_association = fields.Char('Association', required=False)

    marital_status = fields.Selection(selection=_MARITALS, string='Marital Status', required=False)
    depends = fields.Selection(selection=_DEPENDS, string='Depends', required=False, on_change='onchange_depends')
    number_depends = fields.Char('Number of Depends', required=False, on_change='_check_value_depends')

    is_disease = fields.Boolean(string="لا يعاني من أي مرض")
    is_back = fields.Boolean(string="مشاكل في الظهر والمفصل")
    is_chronic_disease = fields.Boolean(string="أمراض مزمنة لا تهدد الحياة")
    is_not_chronic_disease = fields.Boolean(string="لا يعاني من أمراض مزمنة")
    is_virus_C = fields.Boolean(string="Virus C")
    is_kidney_fail = fields.Boolean(string="فشل كلوي")
    is_cancer = fields.Boolean(string="سرطان")
    is_right = fields.Boolean(string="سليم")
    is_blind = fields.Boolean(string="عمى")
    is_amputation = fields.Boolean(string="بتر")
    is_paralysis = fields.Boolean(string="شلل")
    is_disability = fields.Boolean(string="إعاقة ذهنية")
    is_problem = fields.Boolean(string="مشكلة في اليد أو القدم")
    is_weakness = fields.Boolean(string="ضعف نظر شديد")

    department_rent = fields.Integer('إيجار شقة')
    associations_expenses = fields.Integer('جمعيات')
    device_payments = fields.Integer('أقساط أجهزة')
    water_gas = fields.Integer('مياه وغاز وكهرباء')
    studying_child = fields.Integer('دروس أولاد')
    home_expenses = fields.Integer('مصروف البيت')
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
    
    depts = fields.Selection(selection=_DEPTS, string='DEPTS', required=False)
    total_depts = fields.Float('قيمة الديون')
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
    number_sheep = fields.Integer('Number of Sheep')
    total_earth = fields.Float('قيمة اﻷراضي الزراعية')
    total_cow = fields.Float('قيمة المواشي')

    house_ownership = fields.Selection(selection=_HOUSE_OWNERSHIP, string='House Ownership', required=False)
    house_type = fields.Selection(selection=_HOUSE_TYPE, string='House Type', required=False)
    bathroom = fields.Selection(selection=_BATHROOM, string='', required=False)
    number_room = fields.Integer('Number of Rooms')
    walls = fields.Selection(selection=_WALLS, string='Walls', required=False)
    roof = fields.Selection(selection=_ROOF, string='Roof', required=False)
    
    is_devices = fields.Boolean(string="No Devices")
    is_television = fields.Boolean(string="Television")
    is_fridge = fields.Boolean(string="Fridge")
    is_cooker = fields.Boolean(string="Cooker")
    is_fans = fields.Boolean(string="Fans")
    is_washer = fields.Boolean(string="Washer")
    
    experiences_project = fields.Selection(selection=_EXP_PROJECT, string='Experience in Project', required=False)
    exp_months = fields.Integer('Number of Months of Experience')
    
    #volunteering_id = fields.Many2one('volunteers', 'Responsible Volunteers', track_visibility='onchange')
    #volunteer_id = fields.Many2one('volunteers', 'Related Volunteer', track_visibility='onchange')
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the "
                                  "request.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')
    is_active = fields.Boolean(string="Is Active")
    notes = fields.Text('Notes', required=False)
    story = fields.Text('Family Story', required=False)
    criteria = fields.Text('Acceptance and rejection criteria', required=False)
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")
    user_id = fields.Many2one('res.users', 'Related user', track_visibility='onchange')
    volunteers_ids = fields.One2many('needed.cases.volunteer', 'cases_id',
                               'Volunteers to needed cases',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
    
    drugs = fields.Selection(selection=_DRUGS, string='Drugs', required=False)
    smoking = fields.Selection(selection=_SMOKING, string='Smoking', required=False)
    previous_issues = fields.Selection(selection=_ISSUES, string='Previous Issues', required=False)
    previous_projects =  fields.Selection(selection=_PPROJECTS, string='Previous Projects', required=False)
    what_project = fields.Char('What is Project', required=False)
    trosikle = fields.Text('لو جالك تروسيكل هتعمل بيه ايه ؟', required=False)
    experience_work = fields.Text('هل لديك خبرة في مجال معين او صنعة ؟', required=False)
    profession_trosikle = fields.Selection(selection=_PROFESSION, string='هل تفضل الصنعة أو التروسيكل', required=False)
    static_money = fields.Selection(selection=_MONEY, string='هل تفضل مبلغ شهري ثابت 500 جنية', required=False)
    authorized_opinion = fields.Selection(selection=_OPINION, string='Authorized Opinion', required=False
                                          , onchange="_onchange_opinion(authorized_opinion)")
    authorized_reason = fields.Text('Authorized Reason', required=False)
    _order = 'name'
    
    @api.one
    @api.depends('total_expenses', 'total_income')
    #@api.depends('education', 'project_type', 'gov_id')
    def _accepted2(self):
        inability = self.total_expenses - self.total_income 
        Excess = self.total_income - self.total_expenses
        if (self.education == 1 and self.project_type == 1 and self.gov_id.id != 2 ) or (self.job == 4) or (self.depends == 2) or (self.age > 55) or (self.age < 18) or (self.have_project == 2) or (self.is_virus_C == True) or (self.is_kidney_fail == True) or (self.is_cancer == True) or (self.is_blind == True) or (self.is_amputation == True) or (self.is_paralysis == True) or (self.is_disability == True) or (self.is_problem == True) or (self.is_weakness == True) or (inability >= 500) or (Excess >= 400 ) or (self.depts == 3 and self.total_depts > 10000) or (self.depts == 2 and self.total_depts > 15000) or (self.is_earth == True and self.total_earth >= 20000) or (self.is_cow == True and self.total_cow >= 20000):
            self.accepted2 = 2
        elif (self.education == 1 and self.project_type == 1 and self.gov_id.id == 2):
            self.accepted2 = 1
        else:
            self.accepted2 = 1
     
    @api.one
    @api.depends('person_job','person_craft','family_job','family_craft','family_salary','associations_salary','relatives_salary','department_income','other_income')
    def _total_income(self):
        self.total_income = self.person_job + self.person_craft + self.family_job + self.family_craft + self.family_salary + self.associations_salary +  self.relatives_salary + self.department_income + self.other_income
    
    @api.one
    @api.depends('department_rent','associations_expenses','device_payments','water_gas','studying_child','home_expenses','monthly_dept','other_expenses')
    def _total_expenses(self):
        self.total_expenses = self.department_rent + self.associations_expenses + self.device_payments + self.water_gas + self.studying_child + self.home_expenses +  self.monthly_dept + self.other_expenses
                                  
    def change_colore_on_kanban(self):   
        for record in self:
            record.color = 0
            
    
    @api.multi
    def button_to_accreditation(self):
        for rec in self:
            if rec.authorized_opinion == 1:
                rec.state = 'papers'
            elif  rec.authorized_opinion == 2: 
                rec.state = 'accreditation'
            else:
                rec.state = 'accreditation' 
        return True

    @api.multi
    def button_to_papers(self):
        for rec in self:
            rec.state = 'papers'
        return True
    
    @api.multi
    def button_to_drugs(self):
        for rec in self:
            rec.state = 'drugs'
        return True

    @api.multi
    def button_execution(self):
        for rec in self:
            rec.state = 'execution'
        return True
    
    @api.multi
    def button_follow(self):
        for rec in self:
            rec.state = 'follow'
        return True
    
    @api.multi
    def button_research(self):
        for rec in self:
            rec.state = 'research'
        return True
    
    @api.one
    @api.depends('state')    
    @api.onchange('authorized_opinion')
    def _onchange_opinion(self):
        if self.authorized_opinion == 1:
            self.state = 'papers'
        else:
            statess = self.state
            self.state = statess
    
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
    phone = fields.Char(related='volunteer_id.mobile_phone', string='Mobile Phone')
    date_start = fields.Date(string='Start Date', readonly=True,default=fields.Date.context_today,
                             store=True)
    date_finish = fields.Date(string='Finish Date', required=False,
                                track_visibility='onchange')
    is_active = fields.Boolean(string="Is active",
                                 readonly=False)
