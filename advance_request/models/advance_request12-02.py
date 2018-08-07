# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models, _
import urlparse, os
import datetime
from openerp.exceptions import UserError, ValidationError
from openerp.tools import float_is_zero, float_compare
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp

_STATES = [
    (1, 'Draft'),
    (2, 'Assign Direct Manager'),
    (3, 'Assign Head of Department'),
    (4, 'Budget Holder'),
    (5, 'Approve Waver'),
    (6, 'Assign Head of Finance'),
    (7, 'Finance Approved'),
    (8, 'CEO Approved'),
    (9, 'Rejected'),
    (10, 'Validate'),
    (11,'Remain')
]


_STATES_SETTLEMENT = [
    (1, 'Draft'),
    (2, 'Validate')
]

_STAGES = [
    (1, 'Draft'),
    (2, 'Assign Direct Manager'),
    (3, 'Assign Head of Department'),
    (4, 'Budget Holder'),
    (5, 'Approve Waver'),
    (6, 'Assign Head of Finance'),
    (7, 'Finance Approved'),
    (8, 'CEO Approved'),
    (9, 'Rejected'),
    (10,'Validate'),
    (11,'Remain')
]


_TYPES = [
    (1, 'Normal'),
    (2, 'Urgent'),
    (3, 'Exception')
]

class AdvanceRequest(models.Model):

    _name = 'advance.request'
    _description = 'Advance Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _company_get(self):
        company_id = self.env['res.company']._company_default_get(self._name)
        return self.env['res.company'].browse(company_id.id)
    
    @api.model
    def _default_currency(self):
        company = self.env['res.company']._company_default_get('advance.request')
        return company.currency_id

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)
    
    @api.model
    @api.depends('requested_by')
    def _get_default_employee(self):
        for advance in self:
            requested_by = advance.requested_by.id
        #self.employee_id = 
            self.env.cr.execute("SELECT count(hr_employee.id) FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(advance.requested_by.id))
            res0 = self.env.cr.fetchone()[0]
            if res0 == 1:
                self.env.cr.execute("SELECT hr_employee.id FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(advance.requested_by.id))
                res = self.env.cr.fetchone()[0]
                advance.employee_id = res

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('advance.request')

    @api.model
    def _get_default_origin(self):
        for rec in self:
            rec.origin = rec.name

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or \
            self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'),
                                     ('warehouse_id', '=', False)])
        return types[:1]

    @api.multi
    @api.depends('state')
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in (2,3,4,5,6,7,8,9,10,11):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.multi
    def _track_subtype(self, init_values):
        for rec in self:
            if 'state' in init_values and rec.state == 2:
                return 'advance_request.mt_advance_to_approve'
            elif 'state' in init_values and rec.state == 3:
                return 'advance_request.mt_advance_to_department_manager_approved'
            elif 'state' in init_values and rec.state == 4:
                return 'advance_request.mt_advance_to_accountant_manager_approved'
            elif 'state' in init_values and rec.state == 5:
                return 'advance_request.mt_advance_approved'
            elif 'state' in init_values and rec.state == 7:
                return 'advance_request.mt_advance_rejected'
        return super(AdvanceRequest, self)._track_subtype(init_values)
    
    @api.multi
    @api.depends('request_line_ids.request_amount')
    def _compute_amount_all(self):
        for request in self:
            for line in request.request_line_ids: 
                request.amount_requested += line.request_amount
    
    name = fields.Char('Advance Reference', size=32, required=True,
                       default=_get_default_name,track_visibility='onchange')
    origin = fields.Char('Source Document', size=32, compute=_get_default_origin)
    reject_reason = fields.Char('reject_reason', default=' ')
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the request.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')
    date_finish = fields.Date('Expected date of Return',
                             help="Date when the Request will Return.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')
    requested_by = fields.Many2one('res.users','Requestor',required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    employee_id = fields.Many2one('hr.employee', string='Staff ID',
                                   compute="_get_default_employee")
    employee_position = fields.Many2one('hr.job', string='Position',
                                   related='employee_id.job_id')
    
    assigned_to = fields.Many2one('res.users', 'Head of Department',
                                   store=True, related='department.manager_user',
                                  track_visibility='onchange')
    
    assigned_to_3 = fields.Many2one('res.users', 'Project Officer',
                                  related='project.manager_user',
                                  track_visibility='onchange')
    description = fields.Text('Purpose of Advance')
    direct_manager_notes = fields.Text('Direct manager notes')
    department_manager_notes = fields.Text('Department manager notes')
    #purchase_manager_notes = fields.Text('Purchases manager notes')
    #warehouse_manager_notes = fields.Text('Warehouse manager notes')
    accountant_manager_notes = fields.Text('Head of Finance notes')
    executive_manager_notes = fields.Text('Executive manager notes')
    treasurer_manager_notes = fields.Text('Treasurer notes')
    budget_holder_notes = fields.Text('Budget Holder notes')
    company_id = fields.Many2one('res.company', 'Company',required=True,
                                 default=_company_get, track_visibility='onchange')
    #line_ids = fields.One2many('purchase.request.line', 'request_id',
     #                          'Products to Purchase',
      #                         readonly=False,
       #                        copy=True,
        #                       track_visibility='onchange')
    state = fields.Selection(selection=_STATES,string='Status',index=True,
                             track_visibility='onchange',copy=False,default=1)
    stage = fields.Selection(selection=_STAGES,default=1,string='Stage')
    debit_account = fields.Many2one('account.account',string='Debit Account')
    credit_account = fields.Many2one('account.account',string='Credit Account')
    analytic_account = fields.Many2one('account.analytic.account',string='Analytic Account')
    move_id = fields.Many2one('account.move', string='Account Move', readonly=True, copy=False)
    #stock_warehouse = fields.Selection(selection=_WAREHOUSES,
     #                        string='Stock',on_change="onchange_stock(stock_warehouse)")
    #stock_warehouse = fields.ٍSelection(selection=_WAREHOUSES,string='Stock')
    #steps = fields.Selection(selection=_STEPS,
     #                       string='Technical Specifications Steps')
    request_type = fields.Selection(selection=_TYPES,default=1,string='Request Type',
                                    help = 'Provide request as soon as possible :عاجل')
    type_reason = fields.Text('Reason')
    explain_type = fields.Char('Explain',compute='_compute_explain')
    department = fields.Many2one('hr.department', 'Department',
                                 track_visibility='onchange')
    project = fields.Many2one('hr.department', 'Project/Section',
                                  track_visibility='onchange')
    budget_id = fields.Many2one('crossovered.budget' , string='Budget')
    #assigned_to_2 = fields.Many2one('hr.employee', 'Head of Department2',
     #                              store=True, related='department.manager_id',
      #                            track_visibility='onchange')
    assigned_to_2 = fields.Many2one('res.users', 'Budget Holder',
                                   store=True, 
                                  track_visibility='onchange')
    is_editable = fields.Boolean(string="Is editable",compute="_compute_is_editable",
                                 readonly=True)
    line_ids = fields.One2many('advance.settlement', 'advance_id', string='Settlements Lines', copy=True)
    
    request_line_ids = fields.One2many('advance.request.line', 'request_id', string='Advance Lines', copy=True)
    
    settlement_amount = fields.Float(compute='_compute_total', string='Settlement Amount',
       store=True, readonly=True)
    ontime = fields.Integer(string='On Time',compute="change_ontime",readonly=True)
    
    ontime_stage = fields.Integer(string='On Time Stage',compute="change_ontime_stage",readonly=True)
    
    done1= fields.Char(string='Done',compute="change_done_stage",default='early')
    
    progress = fields.Float(string='Progress',compute='change_progress',readonly=True)
    
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
        track_visibility='onchange', ondelete='restrict',
        default=_default_currency)
    
    amount_requested = fields.Float( string='Amount Requested', compute='_compute_amount_all', store=True)
    #price_alltotal = fields.Float( string='Total Amount', compute='_compute_amount_all', store=True)

    #budget_id = fields.Many2one('crossovered.budget' , string='Budget')
    #total_budget = fields.Float(related='budget_id.total_cost', string="Budget Amount")
    #total_budget = fields.Float(related='budget_id.total_cost', string="Total Cost", store=True)
    #budget_drc = fields.Many2one('account.budget.post', string="DRC")
    #total_drc = fields.Float(related='budget_id.total_cost', string="Total Cost")
    #budget_dea = fields.Many2one('crossovered.budget.lines', string='DEA')
    #total_dea = fields.Float(related='budget_dea.planned_amount', string="DEA Amount")
    #dea_availability = fields.Float(related='budget_dea.budget_availability', string="DRC Availability")
    
    cheque = fields.Boolean(string="Cheque")
    bank_transfer = fields.Boolean(string="Bank Transfer")
    cash = fields.Boolean(string="Cash")
    cheque_number = fields.Char(string="Cheque Number")
    transfer_reference = fields.Char(string="Transfer Reference")
    outstand_advance = fields.Boolean(string="Requestor does not already have an outstanding advance")
    exceed_maximum = fields.Boolean(string="Advance does not exceed maximum allocation")
    coding_correct = fields.Boolean(string="Coding correct")
    authorised_dfa = fields.Boolean(string="Authorised per DEA")
    
    is_direct_notes = fields.Boolean(string="Is Direct Notes",
                                 compute="_compute_is_direct_notes",
                                 readonly=True)
    is_dept_notes = fields.Boolean(string="Is Dept Notes",
                                 compute="_compute_is_dept_notes",
                                 readonly=True)
    is_account_notes = fields.Boolean(string="Is Accountant Notes",
                                 compute="_compute_is_account_notes",
                                 readonly=True)
    is_treasure_notes = fields.Boolean(string="Is Treasure Notes",
                                 compute="_compute_is_treasure_notes",
                                 readonly=True)
    is_holder_notes = fields.Boolean(string="Is Holder Notes",
                                 compute="_compute_is_holder_notes",
                                 readonly=True)
    is_executive_notes = fields.Boolean(string="Is Executive Notes",
                                 compute="_compute_is_executive_notes",
                                 readonly=True)
    is_usr = fields.Boolean(string="Is Requested by User",
                                 compute="_compute_is_usr",
                                 readonly=True)
    is_stage = fields.Boolean(string="Is Stage User",
                                 compute="_compute_is_stage",
                                 readonly=True)
    is_required = fields.Boolean(string="Is Required User",
                                 compute="_compute_is_required",
                                 readonly=True)
    is_dept_approve = fields.Boolean(string="Is Dept Approve",
                                 compute="_compute_is_dept_approve",
                                 readonly=True)
    is_reject_required = fields.Boolean(string="Is Reject Required User")
    is_request_approval =  fields.Boolean(string="Is Request_Approval User",
                                 compute="_compute_is_request_approval",
                                 readonly=True)
    
    total_budget = fields.Float(compute='_compute_budget',store=True)
    total_drc = fields.Float(compute='_compute_drc',store=True)
    budget_availability = fields.Float(compute='_compute_budget_availability',store=True)
    drc_availability = fields.Float(compute='_compute_drc_availability',store=True)
    dea_availability = fields.Float(compute='_compute_dea_availability',store=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method')
    
    is_draft = fields.Boolean(string="Is Draft", compute="_compute_is_draft",readonly=True)
    is_assign_direct_Manager = fields.Boolean(string="Is Assign Direct Manager", compute="_compute_is_assign_direct_Manager",readonly=True)
    is_assign_head_of_department = fields.Boolean(string="Is Assign Direct Manager", compute="_compute_is_assign_head_of_department",readonly=True)
    is_assign_cfo_manager = fields.Boolean(string="Is Assign CFO Manager", compute="_compute_is_assign_cfo_manager",readonly=True)
    is_cfo_approved = fields.Boolean(string='CFO Approved', compute='_compute_is_cfo_approved',readonly=True)
    is_assign_budget_holder = fields.Boolean(string='Budget Holder Approve', compute='_compute_is_budget_holder')
    is_approved = fields.Boolean(string='Approved',compute='_is_approved',readonly=True)
    is_rejected = fields.Boolean(string='Rejected',compute='_is_rejected',readonly=True)
    is_finance = fields.Boolean(string='Finance Group',compute='_compute_is_finance_group',readonly=True)
    
    @api.depends('state')
    def _compute_is_draft(self):
        for record in self:
            if record.state == 1:
               record.is_draft = True
               
    @api.depends('state')
    def _compute_is_assign_direct_Manager(self):
        for record in self:
            if record.state == 2:
               record.is_assign_direct_Manager = True
               
    @api.depends('state')
    def _compute_is_assign_head_of_department(self):
        for record in self:
            if record.state == 3:
               record.is_assign_head_of_department = True
               
    @api.depends('state')
    def _compute_is_assign_cfo_manager(self):
        for record in self:
            if record.state == 6:
               record.is_assign_cfo_manager = True
               
    @api.depends('state')
    def _compute_is_budget_holder(self):
        for record in self:
            if record.state == 4:
               record.is_assign_budget_holder = True
               
    @api.depends('state')
    def _compute_is_cfo_approved(self):
        for record in self:
            if record.state == 7:
               record.is_cfo_approved = True
    
    @api.depends('state')
    def _is_approved(self):
        for record in self:
            if record.state == 8:
               record.is_approved = True
               
    @api.depends('state')
    def _is_rejected(self):
        for record in self:
            if record.state == 9:
               record.is_rejected = True
               
    #@api.depends('budget_id')
    #def _compute_budget(self):
     #   for record in self:
      #      record.total_budget = record.budget_id.total_cost
       #     print record.total_budget
            
    @api.multi
    @api.depends('line_ids','line_ids.settlement_amount')
    def _compute_total(self):
        for advance in self:
            line_total = 0.0
            total = 0.0
            for line in advance.line_ids:
                line_total = line.settlement_amount
                total += line_total
            advance.settlement_amount = total
            
    #@api.depends('budget_drc')
    #def _compute_drc(self):
     #   for record in self:
      #      record.total_drc = record.budget_drc.total_cost
       #     print record.total_drc
    
    #@api.depends('budget_id')
    #def _compute_budget_availability(self):
     #   for record in self:
      #      record.budget_availability = record.budget_id.total_availability
       #     print record.budget_availability
    
    #@api.depends('budget_drc')
    #def _compute_drc_availability(self):
     #   for record in self:
      #      record.drc_availability = record.budget_drc.total_availability
       #     print record.drc_availability
    
    #@api.depends('budget_dea')
    #def _compute_dea_availability(self):
     #   for record in self:
      #      record.dea_availability = record.budget_dea.budget_availability
       #     print record.dea_availability
        
    @api.multi
    @api.depends('requested_by')    
    def _compute_is_request_approval(self):
        for rec in self:
            #dep_mang = self.env['res.users'].browse(['res.users'].x_department_manager)
            usr = self.env['res.users'].browse(self.env.uid)
            if usr == rec.requested_by and rec.state == 1:
                rec.is_request_approval = True
            elif usr == rec.requested_by and rec.state != 1:
                rec.is_request_approval = False
            elif usr != rec.requested_by and rec.state == 1:
                rec.is_request_approval = False
            elif usr != rec.requested_by and rec.state != 1:
                rec.is_request_approval = False
            #elif 'res.user.x_department_manager' == True:
             #   rec.is_required = True
            else:
                    rec.is_request_approval = False
    @api.multi
    @api.depends('requested_by')            
    def _compute_is_required(self):
        for rec in self:
            #dep_mang = self.env['res.users'].browse(['res.users'].x_department_manager)
            usr = self.env['res.users'].browse(self.env.uid)
            if usr in rec.assigned_to :
                rec.is_required = True
            #elif 'res.user.x_department_manager' == True:
             #   rec.is_required = True
            else:
                rec.is_required = False
    @api.multi
    @api.depends('requested_by')
    def _compute_is_stage(self):
        for rec in self:
            usr = self.env['res.users'].browse(self.env.uid)
            if usr.has_group('__export__.res_groups_56'):
                rec.is_stage = True
            elif usr.has_group('__export__.res_groups_82'):
                rec.is_stage = True
            else:
                if usr.has_group('__export__.res_groups_59'):
                    rec.is_stage = True
                else:
                    rec.is_stage = False
                    
    @api.depends('request_type')
    def _compute_explain(self):
        for rec in self:
            if rec.request_type == 2:
                rec.explain_type = 'Provide request as soon as possible'
            elif rec.request_type == 3:
                rec.explain_type = 'For project and time conditions, the request is made exceptionally from the rules of the regulation'
            else:
                rec.explain_type = ''
    
    @api.multi
    @api.depends('requested_by')            
    def _compute_is_usr(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_usr = True
            else:
                rec.is_usr = False

    @api.multi
    @api.depends('requested_by')
    def _compute_is_direct_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_direct_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_62'):
                    rec.is_direct_notes = True
                else:
                    rec.is_direct_notes= False
                    
    @api.multi
    @api.depends('requested_by')
    def _compute_is_finance_group(self):
        for rec in self:
            user = self.env['res.users'].browse(self.env.uid)
            if user.has_group('advance_request.group_advance_request_finance'):
                rec.is_finance = True
            else:
                rec.is_finance= False
                    
    @api.multi
    @api.depends('requested_by')                
    def _compute_is_dept_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_dept_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_61'):
                    rec.is_dept_notes = True
                else:
                    rec.is_dept_notes= False
    @api.multi
    @api.depends('requested_by')                
    def _compute_is_dept_approve(self):
        for rec in self:
            if rec.assigned_to == self.env['res.users'].browse(self.env.uid):
                rec.is_dept_approve = True
            else:
                rec.is_dept_approve = False
    
    @api.multi
    @api.depends('requested_by')                
    def _compute_is_account_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_account_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_59'):
                    rec.is_account_notes = True
                else:
                    rec.is_account_notes= False
    
    @api.multi
    @api.depends('requested_by')                
    def _compute_is_treasure_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_treasure_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_63'):
                    rec.is_treasure_notes = True
                else:
                    rec.is_treasure_notes= False
    @api.multi
    @api.depends('requested_by')
    def _compute_is_holder_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_holder_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('advance_request.group_advance_request_budget_holder'):
                    rec.is_holder_notes = True
                else:
                    rec.is_holder_notes= False
    @api.multi
    @api.depends('requested_by')
    def _compute_is_executive_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_executive_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('purchase_request.group_purchase_request_manager'):
                    rec.is_executive_notes = True
                else:
                    rec.is_executive_notes= False
    
    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': '1',
            'name': self.env['ir.sequence'].get('purchase.request'),
        })
        return super(AdvanceRequest, self).copy(default)

    @api.model
    def create(self, vals):
        request = super(AdvanceRequest, self).create(vals)
        if vals.get('assigned_to'):
            request.message_subscribe_users(user_ids=[request.assigned_to.id])
        return request

    @api.multi
    def write(self, vals):
        res = super(AdvanceRequest, self).write(vals)
        for request in self:
            if vals.get('assigned_to'):
                self.message_subscribe_users(user_ids=[request.assigned_to.id])
        return res

    @api.multi
    def button_draft(self):
        for rec in self:
            #rec.state = 'draft'
            #rec.stage = 1
            
            if self.state == 2 and self.direct_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 3 and self.department_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 4 and self.budget_holder_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 6 and self.accountant_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
            elif self.state == 7 and self.executive_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
            elif self.state == 8 and self.executive_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
            else:
                if self.state == 2:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 3:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 4:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 5:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 6:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 7:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 8:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
        return True

    @api.multi
    def button_to_approve(self):
        for rec in self:
            if rec.amount_requested > 0:
                if rec.assigned_to_3:
                    rec.state = 2
                    rec.stage = 2
                    rec.is_reject_required = False
                elif rec.assigned_to_3 == 0:
                    rec.state = 3
                    rec.stage = 3
                    rec.is_reject_required = False
                else:
                    if rec.assigned_to:
                        rec.state = 3
                        rec.stage = 3
                        rec.is_reject_required = False
                    elif rec.assigned_to == 0:
                        rec.state = 4
                        rec.stage = 4
                        rec.is_reject_required = False
                    else:
                        rec.state = 4
                        rec.stage = 4
                        rec.is_reject_required = False
            else:
                rec.reject_reason = 'You Must Write Amount for Advance'
                rec.is_reject_required = True
            for rec_line in rec.request_line_ids:
                rec_line.request_state = rec.state
                
                #if rec.assigned_to_3:
                 #   rec_line.request_state = 2
                #elif rec.assigned_to_3 == 0:
                 #   rec_line.request_state = 3
                #else:
                 #   if rec.assigned_to:
                  #      rec_line.request_state = 3
                   # elif rec.assigned_to == 0:
                    #    rec_line.request_state = 4
                    #else:
                     #   rec_line.request_state = 4
        #else:
         #        raise UserError(_(
          #          "Cannot Request because budget not enough this request !"))         
        return True
    
    @api.multi
    def button_to_department_manager_approved(self):
        for rec in self:
            rec.state = 3
            rec.stage = 3
            rec.is_reject_required = False
            for rec_line in rec.request_line_ids:
                rec_line.request_state = rec.state
        return True
    
    @api.multi
    def button_to_budget_holder_approved(self):
        for rec in self:
            rec.state = 4
            rec.stage = 4
            rec.is_reject_required = False
            for rec_line in rec.request_line_ids:
                rec_line.request_state = rec.state
        return True
    
    @api.multi
    def button_to_accountant_manager_approved(self):
        for rec in self:
            rec.state = 6
            rec.stage = 6
            rec.is_reject_required = False
            for rec_line in rec.request_line_ids:
                rec_line.request_state = rec.state
            #rec.state = 'to_accountant_manager_approved'
            #rec.stage = 3
            #rec.is_reject_required = False
        return True
    
    @api.multi
    def button_approved(self):
        for rec in self:
            rec.state = 8
            rec.stage = 8
            rec.is_reject_required = False
            for rec_line in rec.request_line_ids:
                rec_line.request_state = rec.state
            #rec.state = 'approved'
            #rec.stage = 5
            #rec.is_reject_required = False
        return True
    
    @api.multi
    def button_ceo_approved(self):
        for rec in self:
            rec.state = 7
            rec.stage = 7
            rec.is_reject_required = False
            for rec_line in rec.request_line_ids:
                rec_line.request_state = rec.state
        return True

    @api.multi
    def button_rejected(self):
        for rec in self:
            if self.state == 2 and self.direct_manager_notes != False:
                rec.state = 9
                rec.stage = 9
                rec.is_reject_required = False
                for rec_line in rec.request_line_ids:
                    rec_line.request_state = rec.state
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 3 and self.department_manager_notes != False:
                rec.state = 9
                rec.stage = 9
                rec.is_reject_required = False
                for rec_line in rec.request_line_ids:
                    rec_line.request_state = rec.state
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 4 and self.accountant_manager_notes != False:
                rec.state = 9
                rec.stage = 9
                rec.is_reject_required = False
                for rec_line in rec.request_line_ids:
                    rec_line.request_state = rec.state
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 5 and self.accountant_manager_notes != False:
                rec.state = 9
                rec.stage = 9
                rec.is_reject_required = False
                for rec_line in rec.request_line_ids:
                    rec_line.request_state = rec.state
            elif self.state == 6 and self.executive_manager_notes != False:
                rec.state = 9
                rec.stage = 9
                rec.is_reject_required = False
                for rec_line in rec.request_line_ids:
                    rec_line.request_state = rec.state
            else:
                if self.state == 2:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 3:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 4:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 5:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
                elif self.state == 6:
                    rec.reject_reason = 'You Could Write Reject Reason In notes'
                    rec.is_reject_required = True
        return True
    
   # _constraints = [
    #    (button_rejected, '"You can reject request after write reason in notes :".'),
        
    #(legacy_doc1_getFilename, '"The file must be a JPG file".'),
#]
    @api.multi
    def _check_the_date(self):
        #for rec in self:
         #   d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
          #  new_date = d1 + datetime.timedelta(days=18)
           # rec.date_finish = new_date
        for rec in self:
            if rec.amount_requested <= 500 and rec.amount_requested > 0 and (rec.state == 4 or rec.state == 5):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=6)
                rec.date_finish = new_date
            elif rec.amount_requested > 500 and rec.amount_requested <= 5000 and (rec.state == 4 or rec.state == 5):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=6)
                rec.date_finish = new_date
            elif rec.amount_requested > 5000 and rec.amount_requested <= 100000 and (rec.state == 4 or rec.state == 5):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=12)
                rec.date_finish = new_date
            elif rec.amount_requested > 100000 and (rec.state == 4 or rec.state == 5):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=35)
                rec.date_finish = new_date
            else:
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d')
                rec.date_finish = new_date

    def change_progress(self):
        for rec in self:
            x = rec.stage
            if rec.stage == 8:
                y = 0
            elif rec.stage == 1:
                y = 0
            else:
                y = x * 100 / 14
            rec.progress= y
    
    def change_ontime(self):
        for rec in self:
            if rec.stage == 14 or rec.stage == 8:
                rec.ontime = rec.ontime
            else:
                if rec.state == 5:
                    d1 = datetime.datetime.today()
                    d2 = datetime.datetime.strptime((rec.date_finish),'%Y-%m-%d') 
                    d = str((d2-d1).days + 1)
                    rec.ontime = d
                else:
                    rec.ontime = 0

    def change_ontime_stage(self):
        for rec in self:
            d1 = datetime.datetime.today()
            d2 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
            d = str((d1-d2).days + 1)
            rec.ontime_stage = d
    def change_done_stage(self):
        for rec in self:
            if rec.amount_requested <= 500:
                if rec.stage == 1 and rec.ontime_stage > 1:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==2 and rec.ontime_stage > 2:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==3 and rec.ontime_stage > 4:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==4 and rec.ontime_stage > 4:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==5 and rec.ontime_stage > 4:
                    dd = "late"
                    rec.done1 = dd
                #elif rec.stage ==6 and rec.ontime_stage > 4:
                 #   dd = "late"
                  #  rec.done1 = dd
            elif rec.amount_requested > 500 and rec.amount_requested <= 5000:
                if rec.stage == 1 and rec.ontime_stage > 1:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==2 and rec.ontime_stage > 2:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==3 and rec.ontime_stage > 5:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==4 and rec.ontime_stage > 5:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==5 and rec.ontime_stage > 5:
                    dd = "late"
                    rec.done1 = dd
                #elif rec.stage ==6 and rec.ontime_stage > 5:
                 #   dd = "late"
                  #  rec.done1 = dd
            elif rec.amount_requested > 5000 and rec.amount_requested <= 100000:
                if rec.stage == 1 and rec.ontime_stage > 1:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==2 and rec.ontime_stage > 2:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==3 and rec.ontime_stage > 5:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==4 and rec.ontime_stage > 5:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==5 and rec.ontime_stage > 5:
                    dd = "late"
                    rec.done1 = dd
                #elif rec.stage ==6 and rec.ontime_stage > 5:
                 #   dd = "late"
                  #  rec.done1 = dd
            elif rec.amount_requested > 100000:
                if rec.stage == 1 and rec.ontime_stage > 1:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==2 and rec.ontime_stage > 2:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==3 and rec.ontime_stage > 7:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==4 and rec.ontime_stage > 7:
                    dd = "late"
                    rec.done1 = dd
                elif rec.stage ==5 and rec.ontime_stage > 7:
                    dd = "late"
                    rec.done1 = dd
                #elif rec.stage ==6 and rec.ontime_stage > 7:
                 #   dd = "late"
                  #  rec.done1 = dd
                elif (rec.stage ==6 or rec.stage ==7 or rec.stage ==8 or rec.stage ==9)  and rec.ontime_stage > 8:
                    dd = "late"
                    rec.done1 = dd
                elif (rec.stage ==10 or rec.stage ==11 or rec.stage ==12 or rec.stage ==13)  and rec.ontime_stage > 12:
                    dd = "late"
                    rec.done1 = dd

    def change_colore_on_kanban(self):   
        for record in self:
            color = 0
            if record.progress == 100:
                color = 5
            else:
                if record.ontime < 0:
                    color = 9
                elif record.ontime == 0:
                    if record.state == 4:
                        color = 3
                    elif record.state == 3:
                        color = 3
                    elif record.state == 7:
                        color = 6
                    else:
                        color = 3
                elif record.ontime > 0:
                    color = 5
                elif record.progress == 100:
                    color = 5
                elif record.state == 7:
                    color = 1
            record.color = color
            
    @api.multi
    def write(self,vals):
        # Your logic goes here or call your method
        super(AdvanceRequest, self).write(vals)
        for ss in self:
            if ss.state == 7:
                ss.env.cr.execute("UPDATE advance_request SET stage = 8 WHERE id = '%s' " %(ss.id))
        return True    
    
    
    
    
    @api.model
    def _prepare_move_line_name(self):
        name = _('Advance of %s') % self.employee_id.name
        return name
    
    
    @api.multi
    def _prepare_counterpart_move_line_bank(
            self, name, amount_total_company_cur, total_amount_currency,
            currency_id):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Account')
        if float_compare(
                amount_total_company_cur, 0, precision_digits=precision) == 1:
            debit = amount_total_company_cur
            credit = 0
            total_amount_currency = self.amount_requested
            #credit = amount_total_company_cur
            #debit = 0
            #total_amount_currency = self.amount_total
        else:
            #debit= amount_total_company_cur * -1
            #credit = 0
            #total_amount_currency = self.amount_total * -1
            credit = amount_total_company_cur * -1
            debit = 0
            total_amount_currency = self.amount_requested * -1
        analytic_account_id = self.analytic_account.id
        vals = {
            'debit': debit,
            'credit': credit,
            'name': name,
            #'account_id': self.journal_id.default_debit_account_id.id,
            'account_id': self.debit_account.id,
            'analytic_account_id': analytic_account_id,
            'partner_id': self.requested_by.partner_id.id,
            'currency_id': currency_id,
            'amount_currency': (
                currency_id and total_amount_currency or 0.0),
            }
        return vals
    
    @api.multi
    def _prepare_donation_move_bank_2(
            self, name, amount_total_company_cur, total_amount_currency,
            currency_id):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Account')
        if float_compare(
                amount_total_company_cur, 0, precision_digits=precision) == 1:
            #debit = amount_total_company_cur
            #credit = 0
            #total_amount_currency = self.amount_total
            credit = amount_total_company_cur
            debit = 0
            total_amount_currency = self.amount_requested
        else:
            debit= amount_total_company_cur * -1
            credit = 0
            total_amount_currency = self.amount_requested * -1
            #credit = amount_total_company_cur * -1
            #debit = 0
            #total_amount_currency = self.amount_total * -1
        vals = {
            'debit': debit,
            'credit': credit,
            'name': name,
            #'account_id': self.journal_id.default_debit_account_id.id,
            'account_id': self.credit_account.id,
            'partner_id': self.requested_by.partner_id.id,
            'currency_id': currency_id,
            'amount_currency': (
                currency_id and total_amount_currency or 0.0),
            }
        return vals
    
    @api.multi
    def _prepare_donation_move_bank(self):
        self.ensure_one()
        if not self.debit_account.id:
            raise UserError(
                _("Missing Default Debit Account on advance '%s'.")
                % self.journal_id.name)

        movelines = []
        if self.company_id.currency_id.id != self.currency_id.id:
            currency_id = self.currency_id.id
        else:
            currency_id = False
        name = self._prepare_move_line_name()
        amount_total_company_cur = 0.0
        total_amount_currency = 0.0
        for advance in self:
            amount_total_company_cur = advance.amount_requested
        # counter-part
        ml_vals = self._prepare_counterpart_move_line_bank(
            name, amount_total_company_cur, total_amount_currency,
            currency_id)
        movelines.append((0, 0, ml_vals))
        
        # _prepare_donation_move_bank
        ml_vals_2 = self._prepare_donation_move_bank_2(
            name, amount_total_company_cur, total_amount_currency,
            currency_id)
        movelines.append((0, 0, ml_vals_2))

        vals = {
            'journal_id': self.journal_id.id,
            'date': self.date_start,
            'ref': self.name,
            'line_ids': movelines,
            }
        return vals
    
    @api.one
    def _prepare_analytic_line_bank(self):
        """ Prepare the values used to create() an account.analytic.line upon validation of an account.move.line having
            an analytic account. This method is intended to be extended in other modules.
        """
        tags_id=[]
        #for donation_line in self.line_ids:
            #if donation_line.in_kind:
                #continue
        #amount = (self.credit or 0.0) - (self.debit or 0.0)
        #account_id = self.line_ids.product_id.property_account_income_id.id
        for advance in self:
            account_id = advance.debit_account.id
            analytic_account_id = self.analytic_account.id
            #tags_id = donation_line.tags_id
            
        #if not account_id:
         #   account_id = self.line_ids.product_id.categ_id.property_account_income_categ_id.id    
        name = self._prepare_move_line_name()
        vals = {
            'name': name,
            'date': self.date_start,
            'account_id': analytic_account_id,
            'partner_id': self.requested_by.partner_id.id,
            #'unit_amount': self.quantity,
            #'product_id': self.product_id and self.product_id.id or False,
            #'product_uom_id': self.product_uom_id and self.product_uom_id.id or False,
            'unit_amount': False,
            'product_id': False,
            'product_uom_id': False,
            #'amount': self.company_currency_id.with_context(date=self.date or fields.Date.context_today(self)).compute(amount, self.analytic_account_id.currency_id) if self.analytic_account_id.currency_id else amount,
            'amount': self.amount_requested,
            'general_account_id': account_id,
            'ref': self.name,
            'move_id': self.move_id.id,
            'user_id': self._uid,
            'tag_ids': False
            #'tag_ids': self.tags_id,
        }
        return vals
    
    @api.multi
    def validate(self):
        precision = self.env['decimal.precision'].precision_get('Account')
        for advance in self:
            if not advance.request_line_ids:
                raise UserError(_(
                    "Cannot validate the advance of %s because it doesn't "
                    "have any lines!") % advance.requested_by.partner_id.name)

            if float_is_zero(
                    advance.amount_requested, precision_digits=precision):
                raise UserError(_(
                    "Cannot validate the advance of %s because the "
                    "total amount is 0 !") % self.requested_by.partner_id.name)

            if advance.state != 8:
                raise UserError(_(
                    "Cannot validate the advance of %s because it is not "
                    "in validate state.") % advance.requested_by.partner_id.name)

            vals = {'state': 10}
            if advance.amount_requested:
                move_vals = advance._prepare_donation_move_bank()
                move_analytic_vals = advance._prepare_analytic_line_bank()[0]
                # when we have a full in-kind donation: no account move
                if move_vals:
                    move = self.env['account.move'].create(move_vals)
                    #move.post()
                    move_id2 = move.id
                    vals['move_id'] = move.id
                    
                    #for donation_line in donation.line_ids:
                    analytic_account_id = advance.analytic_account.id
                    if analytic_account_id:
                        move_analytic = self.env['account.analytic.line'].create(move_analytic_vals)
                        move_analytic2 = move_analytic.id            
                        analytic = advance.analytic_account.id
                        account = advance.debit_account.id
                        amount = advance.amount_requested
                         #vals['move_analytic_id'] = move_analytic.id
                        #self.env.cr.execute("insert INTO account_analytic_line_donation_donation_rel(donation_donation_id, account_analytic_line_id) VALUES ('%s','%s')" %(donation_line.donation_id.id,move_analytic.id))
                        
                        self.env.cr.execute("SELECT id FROM account_move_line where move_id = '%s' and account_id ='%d' and analytic_account_id ='%d' " %(move.id,account,analytic))
                    #and analytic_account_id ='%d' , analytic
                        res111 = self.env.cr.fetchone()[0]
                        self.env.cr.execute("UPDATE account_analytic_line set move_id= '%s' where id= '%d'" %(res111,move_analytic.id))
                    #ress = (move.id*2) - 1
                        self.env.cr.execute("UPDATE account_analytic_line set account_id= '%s' where id= '%d'" %(analytic,move_analytic.id))
                        
                        self.env.cr.execute("SELECT credit FROM account_move_line where move_id = '%s' and account_id ='%d' and id ='%d' " %(move.id,account,res111))
                        res111_amount = self.env.cr.fetchone()[0]
                        self.env.cr.execute("UPDATE account_analytic_line set amount= '%s' where id= '%d'" %(amount,move_analytic.id))
                        
                        resss = advance.debit_account.id
                        self.env.cr.execute("UPDATE account_analytic_line set general_account_id= '%s' where id= '%d'" %(resss,move_analytic.id))
                        ressss = advance.requested_by.id
                        self.env.cr.execute("UPDATE account_analytic_line set partner_id= '%s' where id= '%d'" %(ressss,move_analytic.id))          
                else:
                    advance.message_post(_(
                        'Full advance: no account move generated'))
            advance.write(vals)
        return
    
    @api.multi
    def done2cancel(self):
        '''from Done state to Cancel state'''
        for advance in self:
            #if donation.tax_receipt_id:
             #   raise UserError(_(
              #      "You cannot cancel this donation because "
               #     "it is linked to the tax receipt %s. You should first "
                #    "delete this tax receipt (but it may not be legally "
                 #   "allowed).")
                  #  % donation.tax_receipt_id.number)
            if advance.move_id:
                advance.move_id.button_cancel()
                advance.move_id.unlink()
            advance.state = 8
    
class AdvanceRequestLine(models.Model):

    _name = "advance.request.line"
    _description = "Advance Request Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('name','date_required')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in (2,3,4,5,6,7,8,9):
                rec.is_editable = False
            else:
                rec.is_editable = True

    name = fields.Text('Purpose of Advance', size=256, required=True, track_visibility='onchange')
    
    request_amount = fields.Float('Amount', track_visibility='onchange')
    accepted = fields.Boolean('Accepted', track_visibility='onchange')
    request_id = fields.Many2one('advance.request', 'Advance Request', ondelete='cascade', readonly=True)
    company_id = fields.Many2one('res.company', related='request_id.company_id',
                                 string='Company', store=True, readonly=True)
    requested_by = fields.Many2one('res.users', related='request_id.requested_by', string='Requested by',
                                   store=True, readonly=True)
    assigned_to = fields.Many2one('res.users', related='request_id.assigned_to', string='Assigned to',
                                  store=True, readonly=True)
    assigned_to_3 = fields.Many2one('res.users', related='request_id.assigned_to_3', string='Assigned to',
                                  store=True, readonly=True)
    date_start = fields.Date(related='request_id.date_start', string='Request Date', readonly=True,
                             store=True)
    #description = fields.Text(related='request_id.description', string='Description', readonly=True,
     #                         store=True)
    origin = fields.Char(related='request_id.origin', size=32, string='Source Document', readonly=True,
                         store=True)
    date_required = fields.Date(string='Request Date', required=True, track_visibility='onchange',
                                default=fields.Date.context_today)
    is_editable = fields.Boolean(string='Is editable', compute="_compute_is_editable", readonly=True)
    #specifications = fields.Text(string='Specifications')
    #request_state = fields.Selection(selection=_STATES, related='request_id.state',string='Request state', readonly=True,
     #                                store=True)
    
    request_state = fields.Selection(selection=_STATES,string='Request state3', readonly=True,
                                     store=True)
    
    #request_state2 = fields.Selection(string='Request state2',
     #                                readonly=True,
      #                               related='request_id.state',
       #                              selection=_STATES,
        #                             store=True)
    
    request_stage = fields.Selection(string='Request stage', readonly=True, related='request_id.stage',
                                     selection=_STAGES, store=True)
    
    attachment_ids = fields.Many2many('ir.attachment', 'class_ir_attachments_rel', 'class_id', 
                                      'attachment_id', 'Attachments')
    is_accepted = fields.Boolean(string="Is accepted", compute="_compute_is_accepted", store=True 
                                 ,readonly=True)
    
    is_usr = fields.Boolean(string="Is Requested by User", compute="_compute_is_usr", readonly=True)
    
    budget_id = fields.Many2one('crossovered.budget' , string='Budget')
    #total_budget = fields.Float(related='budget_id.total_cost', string="Budget Amount")
    #total_budget = fields.Float(related='budget_id.total_cost', string="Total Cost", store=True)
    budget_drc = fields.Many2one('account.budget.post', string="DRC")
    #total_drc = fields.Float(related='budget_id.total_cost', string="Total Cost")
    budget_dea = fields.Many2one('crossovered.budget.lines', string='DEA')
    
    total_dea = fields.Float(related='budget_dea.planned_amount', string="DEA Amount")
        
    def _compute_is_accepted(self):
        for rec in self:
            if rec.assigned_to == self.env['res.users'].browse(self.env.uid):
                rec.is_accepted = True
            else:
                if rec.assigned_to:
                    rec.is_accepted = False
                elif rec.assigned_to == 0:
                    rec.is_accepted = True
                else:
                    rec.is_accepted = True
          
    def _compute_is_usr(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_usr = True
            else:
                rec.is_usr = False
                
                
    #@api.depends('budget_id')
    #def _compute_budget(self):
     #   for record in self:
      #      record.total_budget = record.budget_id.total_cost
       #     print record.total_budget
            
    @api.multi
    @api.depends('line_ids','line_ids.settlement_amount')
    def _compute_total(self):
        for advance in self:
            line_total = 0.0
            total = 0.0
            for line in advance.line_ids:
                line_total = line.settlement_amount
                total += line_total
            advance.settlement_amount = total
            

            
    @api.depends('budget_drc')
    def _compute_drc(self):
        for record in self:
            record.total_drc = record.budget_drc.total_cost
            print record.total_drc
    
    #@api.depends('budget_id')
    #def _compute_budget_availability(self):
     #   for record in self:
      #      record.budget_availability = record.budget_id.total_availability
       #     print record.budget_availability
    
    @api.depends('budget_drc')
    def _compute_drc_availability(self):
        for record in self:
            record.drc_availability = record.budget_drc.total_availability
            print record.drc_availability
    
    @api.depends('budget_dea')
    def _compute_dea_availability(self):
        for record in self:
            record.dea_availability = record.budget_dea.budget_availability
            print record.dea_availability
                
    
class AdvanceSettlement(models.Model):

    _name = 'advance.settlement'
    _description = 'Advance Settlement'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
   
    advance_id = fields.Many2one('advance.request', string='Advance', ondelete='cascade')
    advance_date = fields.Date(string='Advance Date', related='advance_id.date_start',store=True)
    advance_amount = fields.Float(string='Amount', related='advance_id.amount_requested',store=True)
    advance_employee = fields.Many2one('hr.employee', related='advance_id.employee_id',store=True)
    advance_requestor = fields.Many2one('res.users', related='advance_id.requested_by',store=True)
    advance_date_finish = fields.Date(string='Expected Date of Return', related='advance_id.date_finish',store=True)
    advance_company = fields.Many2one('res.company',string='Office', related='advance_id.company_id',store=True)
    settelment_date = fields.Date(string='Settlement Date')
    settlement_amount = fields.Float(string='Amount', compute='_compute_settlement_amount', store=True)
    #settelment_cheque = fields.Boolean(string="Cheque")
    #settelment_cash = fields.Boolean(string="Cash")
    #settelment_bank = fields.Boolean(string="Bank Transfer")
    #debit_account = fields.Many2one('account.account',string='Debit Account')
    credit_account = fields.Many2one('account.account',string='Credit Account',related='advance_id.debit_account')
    analytic_account = fields.Many2one('account.analytic.account',string='Analytic Account')
    move_id = fields.Many2one('account.move', string='Account Move', readonly=True, copy=False)
    journal_id = fields.Many2one('account.journal', string='Journal')
    #cheque_number = fields.Char(string="Cheque Number")
    #transfer_reference = fields.Char(string="Transfer Reference")
    state = fields.Selection(selection=_STATES_SETTLEMENT,string='Status',index=True,
                             track_visibility='onchange',copy=False,default=1)
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    invoice_partner = fields.Many2one('res.partner',related='invoice_id.partner_id', string="Vendor")
    invoice_date = fields.Date(related='invoice_id.date_invoice', string="Invoice Date")
    invoice_amount = fields.Monetary(string="Invoice Total", related='invoice_id.amount_total')
    currency_id = fields.Many2one('res.currency', string='Currency', related='advance_id.currency_id')
    settlement_lines = fields.One2many('advance.settlement.line', 'settlement_id')
    is_validate = fields.Boolean(string="Is Validate",
                                 compute="_cal_validate",store=True,
                                 readonly=True)
    
    @api.onchange('state')
    def _onchange_allowed_purchase_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders.
        '''
        result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        advance_line_ids = self.settlement_lines.mapped('advance_line_id')
        advance_ids = self.settlement_lines.mapped('advance_id').filtered(lambda r: r.order_line <= advance_line_ids)

        result['domain'] = {'advance_id': [
            ('state', '=', 10),
            ('id', 'not in', advance_ids.ids),
            ]}
        return result
    
    def _prepare_invoice_line_from_po_line(self, line):
 
        invoice_line = self.env['advance.settlement.line']
        data = {
            'advance_line_id': line.id,
            'settlement_purpose': line.name,
            'settlement_amount': line.request_amount,
            'settlement_budget': line.budget_id,
            'settlement_drc':line.budget_drc,
            'settlement_dea':line.budget_dea,
        }
        #account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
        account = 0
        if account:
            data['account_id'] = account.id
        return data
    
    

    # Load all unsold PO lines
    @api.onchange('advance_id')
    def purchase_order_change(self):
        if not self.advance_id:
            return {}
        #if not self.partner_id:
         #   self.partner_id = self.purchase_id.partner_id.id
        settlement_data = self.env['advance.settlement']
        new_lines = self.env['advance.settlement.line']
        #for settlement in self.advance_id:
        #data2 = self._prepare_invoice_from_po_line(self.advance_id)
        #new_line2 = settlement_data.new(data2)

        for line in self.advance_id.request_line_ids - self.settlement_lines.mapped('advance_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.settlement_lines += new_lines
        #self.advance_id = False
        return {}
    
    
    @api.multi
    @api.depends('settlement_lines')
    def _compute_settlement_amount(self):
        for settlement in self:
            amount_total = 0.0
            for line in settlement.settlement_lines:
                line_total = line.settlement_amount2
                amount_total += line_total
            settlement.settlement_amount = amount_total
    
    @api.multi
    @api.depends('settlement_amount','advance_amount')
    def _cal_validate(self):
        for settlement in self:
            if settlement.settlement_amount == settlement.advance_amount:
                settlement.is_validate = True
        
            
   
    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('advance.settlement')
    
    name = fields.Char('Settlement Reference', size=32, required=True,
                       default=_get_default_name,track_visibility='onchange')
    @api.model
    def _prepare_move_line_name(self):
        name = _('Settlement of %s') % self.advance_id.name
        return name
    
    @api.multi
    def _prepare_counterpart_move_line(self, name, settlement_amount, total_amount_currency,currency_id):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Account')
        if float_compare(settlement_amount, 0, precision_digits=precision) == 1:
            #debit = amount_total_company_cur
            #credit = 0
            #total_amount_currency = self.amount_total
            credit = settlement_amount
            debit = 0
            total_amount_currency = self.settlement_amount
        else:
            debit= settlement_amount * -1
            credit = 0
            total_amount_currency = self.settlement_amount * -1
            #credit = amount_total_company_cur * -1
            #debit = 0
            #total_amount_currency = self.amount_total * -1
        vals = {
            'debit': debit,
            'credit': credit,
            'name': name,
            #'account_id': self.journal_id.default_debit_account_id.id,
            'account_id': self.credit_account.id,
            'partner_id': self.advance_requestor.partner_id.id,
            #'partner_id': '',
            'currency_id': currency_id,
            'amount_currency': (currency_id and total_amount_currency or 0.0),
            }
        return vals

    @api.multi
    def _prepare_donation_move(self):
        self.ensure_one()
        if not self.credit_account.id:
            raise UserError(
                _("Missing Default Credit Account on Settlement '%s'.")
                % self.name)

        movelines = []
        if self.advance_company.currency_id.id != self.currency_id.id:
            currency_id = self.currency_id.id
        else:
            currency_id = False
        # Note : we can have negative donations for donors that use direct
        # debit when their direct debit rejected by the bank
        settlement_amount = 0.0
        total_amount_currency = 0.0
        name = self._prepare_move_line_name()
        aml = {}
        
        precision = self.env['decimal.precision'].precision_get('Account')
        for settlement_line in self.settlement_lines:
            settlement_amount += settlement_line.settlement_amount2
            #account_id = donation_line.product_id.property_account_income_id.id
            #if not account_id:
             #   account_id = donation_line.product_id.categ_id.\
              #      property_account_income_categ_id.id
            account_id = settlement_line.debit_account.id
            if not account_id:
                raise UserError(
                    _("Missing debit account on product '%s' or on it's "
                        "related product category")
                    % settlement_line.settlement_id.name)
            #analytic_account_id = settlement_line.get_analytic_account_id()
            
            amount_currency = 0.0
            if float_compare(
                    settlement_line.settlement_amount2, 0,
                    precision_digits=precision) == 1:
                #credit = settlement_line.settlement_amount2
                #debit = 0
                #amount_currency = settlement_line.settlement_amount2 * -1
                debit= settlement_line.settlement_amount2
                credit = 0
                amount_currency = settlement_line.settlement_amount2 * -1
            else:
                #debit = settlement_line.settlement_amount2 * -1
                #credit = 0
                #amount_currency = settlement_line.settlement_amount2
                credit = settlement_line.settlement_amount2 * -1
                debit = 0
                amount_currency = settlement_line.settlement_amount2

            # TODO Take into account the option group_invoice_lines ?
            if (account_id) in aml:
                aml[(account_id)]['credit'] += credit
                aml[(account_id)]['debit'] += debit
                aml[(account_id)]['amount_currency'] \
                    += amount_currency
            else:
                aml[(account_id)] = {
                    'credit': credit,
                    'debit': debit,
                    'amount_currency': amount_currency,
                    }

        if not aml:  # for full in-kind donation
            return False

        for (account_id), content in aml.iteritems():
            movelines.append((0, 0, {
                'name': name,
                'credit': content['credit'],
                'debit': content['debit'],
                'account_id': account_id,
                'analytic_account_id': False,
                'partner_id': self.advance_requestor.partner_id.id,
                'currency_id': currency_id,
                'amount_currency': (
                    currency_id and content['amount_currency'] or 0.0),
                }))

        # counter-part
        ml_vals = self._prepare_counterpart_move_line(
            name, settlement_amount, total_amount_currency,
            currency_id)
        movelines.append((0, 0, ml_vals))

        vals = {
            'journal_id': self.journal_id.id,
            'date': self.settelment_date,
            'ref': self.name,
            'line_ids': movelines,
            }
        return vals

        '''

        # key = (account_id, analytic_account_id)
        # value = {'credit': ..., 'debit': ..., 'amount_currency': ...}
        precision = self.env['decimal.precision'].precision_get('Account')
        for settlement in self:
            #if income_line.in_kind:
             #   continue
            amount_total_company_cur += settlement.settlement_amount
            #account_id = donation_line.product_id.property_account_income_id.id
            #if not account_id:
             #   account_id = donation_line.product_id.categ_id.\
              #      property_account_income_categ_id.id
            #account_id = income_line.get_account_id()
            account_id = self.debit_account.id
            if not account_id:
                raise UserError(
                    _("Missing debit account on Settlement '%s'")
                    % income_line.name)
            #analytic_account_id = donation_line.get_analytic_account_id()
            
            amount_currency = 0.0
            if float_compare(
                    income_line.settlement_amount, 0,
                    precision_digits=precision) == 1:
                #credit = donation_line.amount_company_currency
                #debit = 0
                #amount_currency = donation_line.amount * -1
                debit= income_line.settlement_amount
                credit = 0
                amount_currency = income_line.settlement_amount * -1
            else:
                #debit = donation_line.amount_company_currency * -1
                #credit = 0
                #amount_currency = donation_line.amount
                credit = income_line.settlement_amount * -1
                debit = 0
                amount_currency = income_line.settlement_amount

            # TODO Take into account the option group_invoice_lines ?
            if (account_id) in aml:
                aml[(account_id)]['credit'] += credit
                aml[(account_id)]['debit'] += debit
                aml[(account_id)]['amount_currency'] \
                    += amount_currency
            else:
                aml[(account_id)] = {
                    'credit': credit,
                    'debit': debit,
                    'amount_currency': amount_currency,
                    }

        if not aml:  # for full in-kind donation
            return False

        for (account_id), content in aml.iteritems():
            movelines.append((0, 0, {
                'name': name,
                'credit': content['credit'],
                'debit': content['debit'],
                'account_id': account_id,
                #'analytic_account_id': analytic_account_id,
                'partner_id': self.advance_requestor.partner_id.id,
                'currency_id': currency_id,
                'amount_currency': (
                    currency_id and content['amount_currency'] or 0.0),
                }))

        # counter-part
        ml_vals = self._prepare_counterpart_move_line(
            name, amount_total_company_cur, total_amount_currency,currency_id)
        movelines.append((0, 0, ml_vals))

        vals = {
            'journal_id': self.journal_id.id,
            'date': self.settelment_date,
            'ref': self.name,
            'line_ids': movelines,
            }
        return vals
    '''
    @api.multi
    def validate(self):
        precision = self.env['decimal.precision'].precision_get('Account')
        for settlement in self:
            #if not income.line_ids:
             #   raise UserError(_(
              #      "Cannot validate the income of %s because it doesn't "
               #     "have any lines!") % income.responsible_by.partner_id.name)
            if float_is_zero(
                    settlement.settlement_amount, precision_digits=precision):
                raise UserError(_(
                    "Cannot validate the Settlement of %s because the "
                    "total amount is 0 !") % settlement.advance_requestor.partner_id.name)
            if settlement.state != 1:
                raise UserError(_(
                    "Cannot validate the settlement of %s because it is not "
                    "in draft state.") % settlement.advance_requestor.partner_id.name)
            vals = {'state': 2}
            if settlement.settlement_amount:
                move_vals = settlement._prepare_donation_move()
                if move_vals:
                    move = self.env['account.move'].create(move_vals)
                    move_id2 = move.id
                    vals['move_id'] = move.id
                else:
                    settlement.message_post(_(
                        'Full in-kind advance: no account move generated'))
            settlement.write(vals)
        return
    
class AdvanceSettlementLine(models.Model):

    _name = 'advance.settlement.line'
    _description = 'Advance Settlement Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    advance_line_id = fields.Many2one('advance.request.line', 'Advance Request Line', ondelete='set null', index=True, readonly=True)
    
    advance_id = fields.Many2one('advance.request', related='advance_line_id.request_id', string='Advance Request', store=True, readonly=True, related_sudo=False,
        help='Associated Advance Request. Filled in automatically when a Advance Request .')
    
    settlement_id = fields.Many2one('advance.settlement', string='Advance', ondelete='cascade')
    settelment_date = fields.Date(string='Settlement Date', related='settlement_id.settelment_date')
    settlement_purpose = fields.Char(string="Purpose Of Advance")
    settlement_amount = fields.Float(string="Amount")
    settlement_budget = fields.Many2one('crossovered.budget' , string='Budget')
    settlement_drc = fields.Many2one('account.budget.post', string="DRC")
    settlement_dea = fields.Many2one('crossovered.budget.lines', string='DEA')
    settlement_amount2 = fields.Float(string='Settlement Amount',store=True)
    debit_account = fields.Many2one('account.account',string='Debit Account')
    
    def _set_additional_fields(self,payment):
        """ Some modules, such as Purchase, provide a feature to add automatically pre-filled
            invoice lines. However, these modules might not be aware of extra fields which are
            added by extensions of the accounting module.
            This method is intended to be overridden by these extensions, so that any new field can
            easily be auto-filled as well.
            :param payment : payment.request corresponding record
            :rtype line : payment.request.line record
        """
        pass
    
    
    #@api.onchange('settlement_dea')
    #def _onchange_allowed_purchas_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders.
        '''
     #   result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        #advance_line_ids = self.settlement_lines.mapped('advance_line_id')
      #  advance_ids = self.settlement_dea.mapped('account_ids')

       # result['domain'] = {'debit_account': [
        #    ('account_ids', 'in', advance_ids),
         #   ]}
        #return result