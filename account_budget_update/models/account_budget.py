#from odoo import api, fields, models, _
from openerp import models, fields, api, _
import datetime
from datetime import date, datetime
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
import urlparse, os
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap

import openerp.addons.decimal_precision as dp

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)

class crossovered_budget(models.Model):
    _name = "crossovered.budget"
    _description = "Budget"
    _inherit = ['mail.thread','crossovered.budget']
    _rec_name = "display_name"
    
    @api.multi
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.code:
                name = u'%s [%s] ' % (name, camp.code)
            camp.display_name = name
            
    display_name = fields.Char(string='Display Name', compute='_compute_display_name',readonly=True, store=True)
    project_id = fields.Many2one('project.project',string = 'Project')
    code = fields.Char(string='Code',compute='_compute_code', store = True)
    crossovered_budget = fields.One2many('account.budget.post', 'budget_id', string='DRC', copy=True)
    budget_holder = fields.Many2one('res.users', 'Budget Holder')
    department =  fields.Many2one('hr.department', 'Department', track_visibility='onchange')
    duration = fields.Integer(String='Duration',compute='_compute_duration',store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_amount_all', store=True)
    total_actual = fields.Float(string='Total Actual', compute='_compute_actual_all', store=True)
    total_balance = fields.Float(string='Total Balance', compute='_compute_balance_all', store=True)
    total_applied = fields.Float(string='Total Applied', compute='_compute_applied_all', store=True)
    total_variance = fields.Float(string='Total Variance', compute='_compute_variance_all', store=True)
    total_availability = fields.Float(string='Total Availability', compute='_compute_availability_all', store=True)
    advance_budget_line = fields.One2many('advance.request.line', 'budget_id', 'Advances')
    payment_budget_line = fields.One2many('payment.request.line', 'budget_id', 'Payment Requests')
    total_advance = fields.Float(compute='_compute_amount_advance',string="Total Advance")
    total_payments = fields.Float(compute='_compute_amount_payments',string="Total payments")
    
    @api.multi
    def _compute_amount_availability(self):
        for line in self:
            line.budget_availability = line.total_cost - (line.total_advance + line.total_payments)
                    
    @api.multi
    @api.depends('advance_budget_line.request_amount')
    def _compute_amount_advance(self):
            for line in self:
                for advance in line.advance_budget_line:
                    if isinstance(advance.id, models.NewId):
                        total_advance= 0
                    else:
                        if advance.request_state in  (10,8):
                            line.total_advance += advance.request_amount
                            
    @api.multi
    @api.depends('payment_budget_line.price_total')
    def _compute_amount_payments(self):
            for line in self:
                for payment in line.payment_budget_line:
                    if isinstance(payment.id, models.NewId):
                        total_payment= 0
                    else:
                        #if payment.state in  (6,8):
                        line.total_payments += payment.price_total
    
    
    @api.multi
    @api.depends('crossovered_budget_line.budget_availability')
    def _compute_availability_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_availability += line.budget_availability
    @api.multi
    @api.depends('crossovered_budget_line.planned_amount')
    def _compute_amount_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_cost += line.planned_amount
    
    
    @api.multi
    @api.depends('crossovered_budget_line.practical_amount')
    def _compute_actual_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_actual += line.practical_amount
    
    @api.multi
    @api.depends('crossovered_budget_line.remain_amount')
    def _compute_balance_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_balance += line.remain_amount
                
                
    @api.multi
    @api.depends('crossovered_budget_line.theoritical_amount')
    def _compute_applied_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_applied += line.theoritical_amount
    
    @api.multi
    @api.depends('crossovered_budget_line.variance_amount')
    def _compute_variance_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_variance += line.variance_amount
    #@api.multi   
    #def create(self,vals):
     #   #Your logic goes here or call your method
     #  res_id = super(account_budget_post, self).create(vals)
      # for ss in crossovered_budget.self:
       #     ss.env.cr.execute("UPDATE account_budget_post SET max_code2 = 'Done' WHERE budget_id = '%f'" %(ss.crossovered_budget.id))
       #return res_id
   
  #  @api.multi   
   # def write(self,vals):
    #    #Your logic goes here or call your method
      # res_id = super(account_budget_post, self).write(vals)
       #for ss in crossovered_budget.self:
        #    ss.env.cr.execute("UPDATE account_budget_post SET max_code2 = 'Done' WHERE budget_id = '%f'" %(ss.crossovered_budget.id,ss.crossovered_budget.id))
       #return res_id
    
    
    @api.depends('date_from','date_to')
    def _compute_duration(self):
        for rec in self:
            if rec.date_from:
                d1 = datetime.strptime((rec.date_from),'%Y-%m-%d')
                if rec.date_to: 
                    d2 = datetime.strptime((rec.date_to),'%Y-%m-%d') 
                    d = str((d2-d1).days + 1)
                    rec.duration = d
            
    @api.one
    @api.depends('project_id')
    def _compute_code(self):
        bg_code=''
        for budget in self:
            if budget.project_id:
                bg_code = budget.project_id.code
                budget.code = 'BG-' + bg_code
                
class account_budget_post(models.Model):
    _name = "account.budget.post"
    _description = "Budget Positions"
    _inherit = ['account.budget.post']
    _rec_name = "display_name"
    
    @api.multi
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.code:
                name = u'%s [%s] ' % (name, camp.code)
            camp.display_name = name
    
    @api.multi
    @api.depends('code', 'name')
    def _compute_id(self):
        for camp in self:
            name = camp.name
            if camp.project_code:
               my_code = camp.project_code
               budget_code = 'DRC-' + str(my_code)
               if isinstance(camp.id, models.NewId):
                    camp.code = budget_code + '-'
               else:
                    camp.code = budget_code + '-' + str(camp.id) 
                    
                    
    
    
       
            
    display_name = fields.Char(string='Display Name', compute='_compute_display_name',readonly=True, store=True)
    code = fields.Char(string='Code',compute='_compute_id', store = True)
    project_id = fields.Many2one('project.project',string = 'Project',related='budget_id.project_id',store=True)
    budget_id = fields.Many2one('crossovered.budget',string = 'Budget')
    project_code = fields.Char(string='Project Code',related='budget_id.project_id.code',store=True)
    max_code = fields.Char(string='Max Code', size=32, compute='_compute_max_code',store=True)
    crossovered_budget_line = fields.One2many('crossovered.budget.lines', 'general_budget_id', 'DEA')
    max_code2 = fields.Char(string='Max Code 2', size=32)
    
    total_cost = fields.Float(string='Total Cost', compute='_compute_amount_all', store=True)
    total_actual = fields.Float(string='Total Actual', compute='_compute_actual_all', store=True)
    total_balance = fields.Float(string='Total Balance', compute='_compute_balance_all', store=True)
    total_applied = fields.Float(string='Total Applied', compute='_compute_applied_all', store=True)
    total_variance = fields.Float(string='Total Variance', compute='_compute_variance_all', store=True)
    total_availability = fields.Float(string='Total Availability', compute='_compute_availability_all', store=True)
    advance_budget_line = fields.One2many('advance.request.line', 'budget_drc', 'Advances')
    payment_budget_line = fields.One2many('payment.request.line', 'budget_drc', 'Payment Requests')
    
    total_advance = fields.Float(compute='_compute_amount_advance',string="Total Advance")
    total_payments = fields.Float(compute='_compute_amount_payments',string="Total payments")
    
    @api.multi
    @api.depends('total_advance','total_payments','total_cost')
    def _compute_amount_availability(self):
        for line in self:
            line.budget_availability = line.total_cost - (line.total_advance + line.total_payments)
                    
    @api.multi
    @api.depends('advance_budget_line.request_amount')
    def _compute_amount_advance(self):
            for line in self:
                for advance in line.advance_budget_line:
                    if isinstance(advance.id, models.NewId):
                        total_advance= 0
                    else:
                        if advance.request_state in  (10,8):
                            line.total_advance += advance.request_amount
                            
    @api.multi
    @api.depends('payment_budget_line.price_total')
    def _compute_amount_payments(self):
            for line in self:
                for payment in line.payment_budget_line:
                    if isinstance(payment.id, models.NewId):
                        total_payment= 0
                    else:
                        #if payment.state in  (6,8):
                        line.total_payments += payment.price_total
    
    @api.multi
    @api.depends('crossovered_budget_line.budget_availability')
    def _compute_availability_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_availability += line.budget_availability
    
    @api.multi
    @api.depends('crossovered_budget_line.planned_amount')
    def _compute_amount_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_cost += line.planned_amount
    
    
    @api.multi
    @api.depends('crossovered_budget_line.practical_amount')
    def _compute_actual_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_actual += line.practical_amount
    
    @api.multi
    @api.depends('crossovered_budget_line.remain_amount')
    def _compute_balance_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_balance += line.remain_amount
                
                
    @api.multi
    @api.depends('crossovered_budget_line.theoritical_amount')
    def _compute_applied_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_applied += line.theoritical_amount
    
    @api.multi
    @api.depends('crossovered_budget_line.variance_amount')
    def _compute_variance_all(self):
        for budget in self:
            for line in budget.crossovered_budget_line: 
                budget.total_variance += line.variance_amount
    
    
    @api.one
    @api.depends('project_id')
    def _compute_max_code(self):
        for budget in self:
            if budget.project_id:
                self.env.cr.execute("SELECT count(id) FROM account_budget_post where project_id ='%s'" %(budget.project_id.id))
                my_number = self.env.cr.fetchone()[0]
                self.env.cr.execute("SELECT code FROM project_project where id='%s'" %(budget.project_id.id))
                my_code = self.env.cr.fetchone()[0]
            else:
                my_number = 0
                my_code = 0
            if my_number > 0:
                self.env.cr.execute("SELECT MAX(max_code) FROM account_budget_post where project_id  ='%s'" %(budget.project_id.id))
                my_first_number = self.env.cr.fetchone()[0]
                if my_first_number > 0 :
                        my_initals = my_first_number
                else:
                    my_initals = 0
            else:
                    my_initals = 0
            code5 = int(my_initals) + 1
    
            if isinstance(budget.id, models.NewId):
                budget.max_code = code5
            #budget.max_code = int(my_initals) + 1
            budget.project_code = my_code
            budget_code = 'DRC-' + str(my_code)
            code2 = int(budget.max_code)
            code3 = '%02d' % code2
            code4 = budget_code+ '-' + code3 
            budget.code =  code4
            
            
    #@api.one
    #@api.depends('project_id')
    #def _compute_max_code(self):
     #   data = {d['id']: d['max_code']
      #      for d in self.read(['max_code'])}
       # for budget in self:
        #    if budget.project_id:
         #       self.env.cr.execute("SELECT count(id) FROM account_budget_post where project_id ='%s'" %(budget.project_id.id))
           #     my_number = self.env.cr.fetchone()[0]
            #    self.env.cr.execute("SELECT code FROM project_project where id='%s'" %(budget.project_id.id))
             #   my_code = self.env.cr.fetchone()[0]
            #else:
             #   my_number = 0
              #  my_code = 0
            #if my_number > 0:
             #   self.env.cr.execute("SELECT MAX(max_code) FROM account_budget_post where project_id  ='%s'" %(budget.project_id.id))
              #  my_first_number = self.env.cr.fetchone()[0]
               # if my_first_number > 0 :
                #        my_initals = my_first_number
                #else:
                 #   my_initals = 0
            #else:
             #       my_initals = 0
            #code5 = int(my_initals) + 1
    
            #if isinstance(budget.id, models.NewId):
             #   budget.max_code = code5
            #else:
             #   budget.max_code = data.get(budget.id, 'default')
            #budget.max_code = int(my_initals) + 1
            #budget.project_code = my_code
            #budget_code = 'DRC-' + str(my_code)
            #code2 = int(budget.max_code)
            #code3 = '%02d' % code2
            #code4 = budget_code+ '-' + code3 
            #budget.code =  code4
            
                #if isinstance(self.id, models.NewId):
                 #   self.max_code = int(my_initals) + 1
                #else:
                 #   self.env.cr.execute("SELECT max_code FROM account_budget_post where project_id  ='%s' and id='%s'" %(self.project_id.id,self.id))
                  #  max_code2 = self.env.cr.fetchone()[0]
                   # self.max_code2 = max_code2
                
    @api.depends('project_id')
    def _compute_code(self):
        for budget in self:
            if budget.project_id:
                self.env.cr.execute("SELECT code FROM project_project where id='%s'" %(budget.project_id.id))
                my_code = self.env.cr.fetchone()[0]
            else:
                my_code = 0
            budget.project_code = my_code
            budget_code = 'DRC-' + str(my_code)
            code2 = int(budget.max_code)
            code3 = '%02d' % code2
            code4 = budget_code+ '-' + code3 
            budget.code =  code4
                            
class crossover_budget_lines(models.Model):
    _name = 'crossovered.budget.lines'
    _inherit = 'crossovered.budget.lines'
    _rec_name = "display_name"
    
    
    @api.depends('planned_amount','practical_amount')
    def _compute_remain(self):
        for budget in self:
            budget.remain_amount = budget.planned_amount - budget.practical_amount
            
    @api.depends('theoritical_amount','practical_amount')
    def _compute_variance(self):
        for budget in self:
            budget.variance_amount = budget.theoritical_amount - budget.practical_amount
    
    def _theo_amt(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            today = datetime.now()
            # Used for the report
            if line.forecast_units > 1:
                theo_amt = (line.planned_amount/line.forecast_units) * line.actual_units
            else:
                if context.get('wizard_date_from') and context.get('wizard_date_to'):
                    date_from = strToDatetime(context.get('wizard_date_from'))
                    date_to = strToDatetime(context.get('wizard_date_to'))
                    if date_from < strToDatetime(line.date_from):
                        date_from = strToDatetime(line.date_from)
                    elif date_from > strToDatetime(line.date_to):
                        date_from = False

                    if date_to > strToDatetime(line.date_to):
                        date_to = strToDatetime(line.date_to)
                    elif date_to < strToDatetime(line.date_from):
                        date_to = False

                    theo_amt = 0.00
                    if date_from and date_to:
                        line_timedelta = strToDatetime(line.date_to) - strToDatetime(line.date_from)
                        elapsed_timedelta = date_to - date_from
                        if elapsed_timedelta.days > 0:
                            theo_amt = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_amount
                else:
                    if line.paid_date:
                        if strToDate(line.date_to) <= strToDate(line.paid_date):
                            theo_amt = 0.00
                        else:
                            theo_amt = line.planned_amount
                    else:

                        line_timedelta = strToDatetime(line.date_to) - strToDatetime(line.date_from)
                        elapsed_timedelta = today - (strToDatetime(line.date_from))

                        if elapsed_timedelta.days < 0:
                            # If the budget line has not started yet, theoretical amount should be zero
                            theo_amt = 0.00
                        elif line_timedelta.days > 0 and today < strToDatetime(line.date_to):
                            # If today is between the budget line date_from and date_to
                            # from pudb import set_trace; set_trace()
                            theo_amt = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_amount
                        else:
                            theo_amt = line.planned_amount

            res[line.id] = theo_amt
        return res
    
    @api.multi
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.code:
                name = u'%s [%s] ' % (name, camp.code)
            camp.display_name = name
            
            
    @api.multi
    @api.depends('forecast_units','cost_unit')
    def _compute_amount(self):
        for budget in self:
            budget.planned_amount = budget.forecast_units * budget.cost_unit
            
            
    #@api.constrains('national_number')
    @api.depends('date_from')
    def _check_value_date_from(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        #pattern = "^\+?[0-9]*$"
        for data in record:
            if data.date_from < data.crossovered_budget_id.date_from:
                #raise ValidationError("You cannot add Start Date less than Budget Start Date")
                return False
        return True
    
    @api.depends('date_to')
    def _check_value_date_to(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        #pattern = "^\+?[0-9]*$"
        for data in record:
            if data.date_to > data.crossovered_budget_id.date_to:
                #raise ValidationError("You cannot add Start Date less than Budget Start Date")
                return False
        return True
    
    _constraints = [
    (_check_value_date_from, '"You cannot add Start Date before Budget Start Date for DEA "', ['date_from']),
    (_check_value_date_to, '"You cannot add End Date after Budget End Date for DEA.', ['date_to']),
]
    
    
    date_from = fields.Date('Start Date', required=True, on_change='_check_value_date_from')
    date_to = fields.Date('End Date', required=True, on_change='_check_value_date_to')        
    display_name = fields.Char(string='Display Name', compute='_compute_display_name',readonly=True, store=True)
    name =  fields.Char('DEA Name', required=True)
    remain_amount = fields.Float('Remain Amount',compute='_compute_remain',Store=True)
    variance_amount = fields.Float('Variance Amount',compute='_compute_variance',Store=True)
    forecast_units = fields.Integer('Forecast Units',store=True,Default=1)
    unit_name =  fields.Char('Unit Name',store=True)
    actual_units = fields.Integer('Actual Units',store=True,Default=0)
    cost_unit = fields.Float('Cost Per Unit',store=True)
    code = fields.Char(string='Code',compute='_compute_code', store = True)
    project_id = fields.Many2one('project.project',string = 'Project',related='crossovered_budget_id.project_id',store=True)
    max_code = fields.Char(string='Max Code', size=32, compute='_compute_max_code',store=True)
    project_code = fields.Char(string='Project Code',compute='_compute_code')
    general_budget_id = fields.Many2one('account.budget.post', 'DRC',required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', related='crossovered_budget_id.project_id.analytic_account_id',store=True)
    planned_amount = fields.Float('Planned Amount', required=True,compute='_compute_amount',store=True)
    notes = fields.Text('Notes')
    account_ids = fields.Many2many('account.account', 'account_budget_dea_rel', 'crossover_budget_line_id', 'account_id', 'Expenses')
    advance_budget_line = fields.One2many('advance.request.line', 'budget_dea', 'Advances')
    payment_budget_line = fields.One2many('payment.request.line', 'budget_dea', 'Payment Requests')
    total_advance = fields.Float(compute='_compute_amount_advance',string="Total Advance")
    total_payments = fields.Float(compute='_compute_amount_payments',string="Total payments")
    budget_availability = fields.Float(compute='_compute_amount_availability',string="Total Availability")
    #assigned_to_3 = fields.Many2one('res.users', 'Project Officer',domain="[('parent_id','=',department)]"
     #                             domain=[('x_project_manager', '=', True)],
      #                            track_visibility='onchange')
      
    @api.multi
    @api.depends('total_advance','total_payments','planned_amount')
    def _compute_amount_availability(self):
        for line in self:
            line.budget_availability = line.planned_amount - (line.total_advance + line.total_payments)
                    
    @api.multi
    @api.depends('advance_budget_line.request_amount')
    def _compute_amount_advance(self):
            for line in self:
                for advance in line.advance_budget_line:
                    if isinstance(advance.id, models.NewId):
                        total_advance= 0
                    else:
                        if advance.request_state in  (10,8):
                            line.total_advance += advance.request_amount
                            
    @api.multi
    @api.depends('payment_budget_line.price_total')
    def _compute_amount_payments(self):
            for line in self:
                for payment in line.payment_budget_line:
                    if isinstance(payment.id, models.NewId):
                        total_payment= 0
                    else:
                        #if payment.state in  (6,8):
                        line.total_payments += payment.price_total
    
    def _prac_amt(self, cr, uid, ids, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            acc_ids = [x.id for x in line.account_ids]
            if not acc_ids:
                raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.name))
            date_to = context.get('wizard_date_to') or line.date_to
            date_from = context.get('wizard_date_from') or line.date_from
            if line.analytic_account_id.id:
                cr.execute("SELECT SUM(amount) FROM account_analytic_line WHERE account_id=%s AND (date "
                       "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                       "general_account_id=ANY(%s)", (line.analytic_account_id.id, date_from, date_to,acc_ids,))
                result = cr.fetchone()[0]
                if result is None:
                    result = 0.0
            else:
                result = 0.0
            res[line.id] = result
        return res
    
    @api.model
    @api.depends('general_budget_id')
    def _compute_max_code(self):
        for budget in self:
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