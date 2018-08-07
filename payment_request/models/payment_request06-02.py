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
    (4, 'Assign CFO Manager'),
    (5, 'CFO Approved'),
    (6,'Approved'),
    (7, 'Rejected')
]

_STAGES = [
    (1, 'Draft'),
    (2, 'Assign Direct Manager'),
    (3, 'Assign Head of Department'),
    (4, 'Assign CFO Manager'),
    (5, 'CFO Approved'),
    (6,'Approved'),
    (7, 'Rejected')
]


_TYPES = [
    (1, 'Normal'),
    (2, 'Urgent'),
    (3, 'Exception')
]

class PaymentRequest(models.Model):

    _name = 'payment.request'
    _description = 'Payment Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _company_get(self):
        company_id = self.env['res.company']._company_default_get(self._name)
        return self.env['res.company'].browse(company_id.id)
    
    @api.model
    def _default_currency(self):
        company = self.env['res.company']._company_default_get('payment.request')
        return company.currency_id

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)
    
    @api.model
    @api.depends('requested_by')
    def _get_default_employee(self):
        
        requested_by = self.requested_by.id
        #self.employee_id = 
        self.env.cr.execute("SELECT count(hr_employee.id) FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(self.requested_by.id))
        res0 = self.env.cr.fetchone()[0]
        if res0 == 1:
            self.env.cr.execute("SELECT hr_employee.id FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(self.requested_by.id))
            res = self.env.cr.fetchone()[0]
            self.employee_id = res

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('payment.request')

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
            if rec.state in (2,3,4,5,7):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.multi
    def _track_subtype(self, init_values):
        for rec in self:
            if 'state' in init_values and rec.state == 2:
                return 'purchase_request.mt_request_to_approve'
            elif 'state' in init_values and rec.state == 3:
                return 'purchase_request.mt_request_to_department_manager_approved'
            elif 'state' in init_values and rec.state == 4:
                return 'purchase_request.mt_request_to_accountant_manager_approved'
            elif 'state' in init_values and rec.state == 5:
                return 'purchase_request.mt_request_approved'
            elif 'state' in init_values and rec.state == 7:
                return 'purchase_request.mt_request_rejected'
        return super(PaymentRequest, self)._track_subtype(init_values)
    
    @api.onchange('state', 'partner_id')
    def _onchange_allowed_purchase_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders.
        '''
        result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        purchase_line_ids = self.line_ids.mapped('purchase_line_id')
        purchase_ids = self.line_ids.mapped('purchase_id').filtered(lambda r: r.order_line <= purchase_line_ids)

        result['domain'] = {'purchase_id': [
            ('invoice_status', '=', 'to invoice'),
            ('partner_id', 'child_of', self.partner_id.id),
            ('id', 'not in', purchase_ids.ids),
            ]}
        return result
    
    
    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['payment.request.line']
        data = {
            'purchase_line_id': line.id,
            'name': line.name,
            'origin': self.purchase_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            #'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            #'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id, round=False),
            'product_price': line.order_id.currency_id.compute(line.price_unit, self.currency_id, round=False),
            #'quantity': qty,
            'product_qty':  line.product_qty,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        #account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
        account = 0
        if account:
            data['account_id'] = account.id
        return data

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['payment.request.line']
        for line in self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.line_ids += new_lines
        self.purchase_id = False
        return {}

    
    name = fields.Char('Payment Reference', size=32, required=True,
                       default=_get_default_name,track_visibility='onchange')
    
    purchase_id = fields.Many2one('purchase.order', string='Add Purchase Order',
        help='Encoding help. When selected, the associated purchase order lines are added to the vendor bill. Several PO can be selected.')
    partner_id = fields.Many2one('res.partner', string='Supplier Name', change_default=True,
        required=True,
        track_visibility='always')
    
    origin = fields.Char('Source Document', size=32, compute=_get_default_origin)
    reject_reason = fields.Char('reject_reason', default=' ')
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the request.",
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
    assigned_to_2 = fields.Many2one('res.users', 'Head of Department',
                                  domain=[('x_department_manager', '=', True)],
                                  track_visibility='onchange')
    #assigned_to_3 = fields.Many2one('res.users', 'Project Officer',
     #                             domain=[('x_project_manager', '=', True)],
      #                            track_visibility='onchange')
    description = fields.Text('Purpose of Request')
    direct_manager_notes = fields.Text('Direct manager notes')
    department_manager_notes = fields.Text('Department manager notes')
    #purchase_manager_notes = fields.Text('Purchases manager notes')
    #warehouse_manager_notes = fields.Text('Warehouse manager notes')
    accountant_manager_notes = fields.Text('CFO notes')
    executive_manager_notes = fields.Text('Executive manager notes')
    treasurer_manager_notes = fields.Text('Treasurer notes')
    budget_holder_notes = fields.Text('Budget Holder notes')
    company_id = fields.Many2one('res.company', 'Office',required=True,
                                 default=_company_get, track_visibility='onchange')
    line_ids = fields.One2many('payment.request.line', 'request_id','Expense Details', readonly=False, copy=True,track_visibility='onchange')
    state = fields.Selection(selection=_STATES,string='Status',index=True,
                             track_visibility='onchange',copy=False,default=1)
    stage = fields.Selection(selection=_STAGES,default=1,string='Stage')
    request_type = fields.Selection(selection=_TYPES,default=1,string='Request Type',
                                    help = 'Provide request as soon as possible :عاجل')
    type_reason = fields.Text('Reason')
    explain_type = fields.Char('Explain',compute='_compute_explain')
    department = fields.Many2one('hr.department', 'Department',
                                 track_visibility='onchange')
    project = fields.Many2one('hr.department', 'Project/Section',
                                  track_visibility='onchange')
    is_editable = fields.Boolean(string="Is editable",compute="_compute_is_editable",
                                 readonly=True)
    
    #ontime = fields.Integer(string='On Time',compute="change_ontime",readonly=True)
    
    #ontime_stage = fields.Integer(string='On Time Stage',compute="change_ontime_stage",readonly=True)
    
    #done1= fields.Char(string='Done',compute="change_done_stage",default='early')
    
    #progress = fields.Float(string='Progress',compute='change_progress',readonly=True)
    
    color = fields.Integer('Color Index', compute="change_colore_on_kanban")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
        track_visibility='onchange', ondelete='restrict',
        default=_default_currency)
    
    #amount_requested = fields.Float( string='Amount Requested')
    
    
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    invoice_partner = fields.Many2one('res.partner',related='invoice_id.partner_id', string="Invoice Partner")
    invoice_date = fields.Date(related='invoice_id.date_invoice', string="Invoice Date")
    invoice_amount = fields.Monetary(string="Invoice Total", related='invoice_id.amount_total')
    cheque = fields.Boolean(string="Cheque")
    bank_transfer = fields.Boolean(string="Bank Transfer")
    cash = fields.Boolean(string="Cash")
    cheque_number = fields.Char(string="Cheque Number")
    transfer_reference = fields.Char(string="Transfer Reference")
    #outstand_payment = fields.Boolean(string="Requestor does not already have an outstanding payment")
    #exceed_maximum = fields.Boolean(string="Advance does not exceed maximum allocation")
    coding_correct = fields.Boolean(string="Coding correct")
    authorised_dfa = fields.Boolean(string="Authorised per DFA")
    payee_correct = fields.Boolean(string="Payee Correct")
    Procurement_procedures = fields.Boolean(string='Procurement Procedures Followed')
    good_received = fields.Boolean(string='Good/Services Received')
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
                                 compute="_compute_is_pres_notes",
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
    
    price_alltotal = fields.Float( string='Total Price', compute='_compute_amount_all', store=True)
    
    is_draft = fields.Boolean(string="Is Draft", compute="_compute_is_draft",readonly=True)
    is_assign_direct_Manager = fields.Boolean(string="Is Assign Direct Manager", compute="_compute_is_assign_direct_Manager",readonly=True)
    is_assign_head_of_department = fields.Boolean(string="Is Assign Direct Manager", compute="_compute_is_assign_head_of_department",readonly=True)
    is_assign_cfo_manager = fields.Boolean(string="Is Assign CFO Manager", compute="_compute_is_assign_cfo_manager",readonly=True)
    is_cfo_approved = fields.Boolean(string='CFO Approved', compute='_compute_is_cfo_approved',readonly=True)
    is_approved = fields.Boolean(string='Approved',compute='_is_approved',readonly=True)
    is_rejected = fields.Boolean(string='Rejected',compute='_is_rejected',readonly=True)
    
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
            if record.state == 4:
               record.is_assign_cfo_manager = True
               
    @api.depends('state')
    def _compute_is_cfo_approved(self):
        for record in self:
            if record.state == 5:
               record.is_cfo_approved = True
    
    @api.depends('state')
    def _is_approved(self):
        for record in self:
            if record.state == 6:
               record.is_approved = True
               
    @api.depends('state')
    def _is_rejected(self):
        for record in self:
            if record.state == 7:
               record.is_rejected = True
    
    #@api.depends('budget_id')
    #def _compute_budget(self):
     #   for record in self:
      #      record.total_budget = record.budget_id.total_cost
       #     print record.total_budget
    
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
    
   # @api.depends('budget_drc')
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
    @api.depends('line_ids.price_total')
    def _compute_amount_all(self):
        for request in self:
            for line in request.line_ids: 
                request.price_alltotal += line.price_total
                
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
    def _compute_is_pres_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_pres_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_65'):
                    rec.is_pres_notes = True
                else:
                    rec.is_pres_notes= False
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
            'name': self.env['ir.sequence'].get('payment.request'),
        })
        return super(PaymentRequest, self).copy(default)

    @api.model
    def create(self, vals):
        request = super(PaymentRequest, self).create(vals)
        if vals.get('assigned_to'):
            request.message_subscribe_users(user_ids=[request.assigned_to.id])
        return request

    @api.multi
    def write(self, vals):
        res = super(PaymentRequest, self).write(vals)
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
            elif self.state == 4 and self.accountant_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 5 and self.accountant_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
            elif self.state == 6 and self.executive_manager_notes != False:
                rec.state = 1
                rec.stage = 1
                rec.is_reject_required = False
            elif self.state == 7 and self.accountant_manager_notes != False:
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
        return True

    @api.multi
    def button_to_approve(self):
        for rec in self:
            if (rec.dea_availability - rec.price_alltotal) > 0:
                if rec.price_alltotal > 0:
                    if rec.assigned_to_3:
                        rec.state = 2
                        rec.stage = 2
                        rec.is_reject_required = False
                    elif rec.assigned_to_3 == 0:
                        rec.state = 3
                        rec.stage = 2
                        rec.is_reject_required = False
                    else:
                        if rec.assigned_to:
                            rec.state = 3
                            rec.stage = 2
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
                    rec.reject_reason = 'You Must Write price Items'
                    rec.is_reject_required = True
            else:
                 raise UserError(_(
                    "Cannot Request because budget not enough this request !"))
        return True
    
    @api.multi
    def button_to_department_manager_approved(self):
        for rec in self:
            if rec.price_alltotal < 5000:
                rec.state = 4
                rec.stage = 3
                rec.is_reject_required = False
            else:
                rec.state = 3
                rec.is_reject_required = False
        return True

    @api.multi
    def button_to_accountant_manager_approved(self):
        for rec in self:
            if rec.price_alltotal < 50000:
                rec.state = 4
                rec.stage = 3
                rec.is_reject_required = False
            else:
                rec.state = 4
                rec.stage = 3
                rec.is_reject_required = False
            #rec.state = 'to_accountant_manager_approved'
            #rec.stage = 3
            #rec.is_reject_required = False
        return True
    
    @api.multi
    def button_approved(self):
        for rec in self:
            if rec.price_alltotal < 50000:
                rec.state = 6
                rec.stage = 5
                rec.is_reject_required = False
            else:
                rec.state = 5
                rec.stage = 5
                rec.is_reject_required = False
            #rec.state = 'approved'
            #rec.stage = 5
            #rec.is_reject_required = False
        return True
    
    @api.multi
    def button_ceo_approved(self):
        for rec in self:
            rec.state = 5
            rec.stage = 5
            rec.is_reject_required = False
        return True

    @api.multi
    def button_rejected(self):
        for rec in self:
            if self.state == 2 and self.direct_manager_notes != False:
                rec.state = 7
                rec.stage = 7
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 3 and self.department_manager_notes != False:
                rec.state = 7
                rec.stage = 7
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 4 and self.accountant_manager_notes != False:
                rec.state = 7
                rec.stage = 7
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 5 and self.accountant_manager_notes != False:
                rec.state = 7
                rec.stage = 7
                rec.is_reject_required = False
            elif self.state == 6 and self.executive_manager_notes != False:
                rec.state = 7
                rec.stage = 7
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
            if rec.price_alltotal <= 500 and rec.price_alltotal > 0 and (rec.state == 4 or rec.state == 5):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=6)
                rec.date_finish = new_date
            elif rec.price_alltotal > 500 and rec.price_alltotal <= 5000 and (rec.state == 4 or rec.state == 5):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=6)
                rec.date_finish = new_date
            elif rec.price_alltotal > 5000 and rec.price_alltotal <= 100000 and (rec.state == 4 or rec.state == 5):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=12)
                rec.date_finish = new_date
            elif rec.price_alltotal > 100000 and (rec.state == 4 or rec.state == 5):
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
            if rec.stage == 15:
                y = 0
            elif rec.stage == 1:
                y = 0
            else:
                y = x * 100 / 14
            rec.progress= y
    


    def change_ontime_stage(self):
        for rec in self:
            d1 = datetime.datetime.today()
            d2 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
            d = str((d1-d2).days + 1)
            rec.ontime_stage = d
    def change_done_stage(self):
        for rec in self:
            if rec.price_alltotal <= 500:
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
            elif rec.price_alltotal > 500 and rec.price_alltotal <= 5000:
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
            elif rec.price_alltotal > 5000 and rec.price_alltotal <= 100000:
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
            elif rec.price_alltotal > 100000:
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
                elif (rec.stage ==6 or rec.stage ==7 or rec.stage ==8 or rec.stage ==9)  and rec.ontime_stage > 15:
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
        super(PaymentRequest, self).write(vals)
        for ss in self:
            if ss.state == 7:
                ss.env.cr.execute("UPDATE payment_request SET stage = 15 WHERE id = '%s' " %(ss.id))
        return True    
    
    
class PaymentRequestLine(models.Model):
    _name = "payment.request.line"
    _description = "Payment Request Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'analytic_account_id', 'date_required', 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in (2,3,4,5,6,7):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.multi
    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.seller_ids:
                    rec.supplier_id = rec.product_id.seller_ids[0].name
                    
    purchase_line_id = fields.Many2one('purchase.order.line', 'Purchase Order Line', ondelete='set null', index=True, readonly=True)
    purchase_id = fields.Many2one('purchase.order', related='purchase_line_id.order_id', string='Purchase Order', store=False, readonly=True, related_sudo=False,
        help='Associated Purchase Order. Filled in automatically when a PO is chosen on the vendor bill.')

    product_id = fields.Many2one('product.product', 'Product',
        domain=[('purchase_ok', '=', True)],track_visibility='onchange')
    name = fields.Char('Description', size=256, required=True, 
                       track_visibility='onchange')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',
                                     track_visibility='onchange')
    product_qty = fields.Float('Quantity', track_visibility='onchange', default = 1,
                               digits_compute=dp.get_precision(
                                   'Product Unit of Measure'))
    product_price = fields.Float('Price', track_visibility='onchange')
    accepted = fields.Boolean('Accepted', track_visibility='onchange')
    request_id = fields.Many2one('payment.request',
                                 'Payment Request',
                                 ondelete='cascade', readonly=True)
    company_id = fields.Many2one('res.company',
                                 related='request_id.company_id',
                                 string='Company',
                                 store=True, readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          track_visibility='onchange')
    requested_by = fields.Many2one('res.users',
                                   related='request_id.requested_by',
                                   string='Requested by',
                                   store=True, readonly=True)
    assigned_to = fields.Many2one('res.users',
                                  related='request_id.assigned_to',
                                  string='Assigned to',
                                  store=True, readonly=True)
    assigned_to_3 = fields.Many2one('res.users',
                                  related='request_id.assigned_to_3',
                                  string='Assigned to',
                                  store=True, readonly=True)
    date_start = fields.Date(related='request_id.date_start',
                             string='Request Date', readonly=True,
                             store=True)
    description = fields.Text(related='request_id.description',
                              string='Description', readonly=True,
                              store=True)
    origin = fields.Char(related='request_id.origin',
                         size=32, string='Source Document', readonly=True,
                         store=True)
    date_required = fields.Date(string='Request Date', 
                                track_visibility='onchange',
                                default=fields.Date.context_today)
    is_editable = fields.Boolean(string='Is editable',
                                 compute="_compute_is_editable",
                                 readonly=True)
    specifications = fields.Text(string='Specifications')
    request_state = fields.Selection(string='Request state',
                                     readonly=True,
                                     related='request_id.state',
                                     selection=_STATES,
                                     store=True)
    request_stage = fields.Selection(string='Request stage',
                                     readonly=True,
                                     related='request_id.stage',
                                     selection=_STAGES,
                                     store=True)
    
    supplier_id = fields.Many2one('res.partner',
                                  string='Preferred supplier',
                                  compute="_compute_supplier_id")

    procurement_id = fields.Many2one('procurement.order',
                                     'Procurement Order',
                                     readonly=True)
    
    attachment_ids = fields.Many2many('ir.attachment', 'class_ir_attachments_rel', 'class_id', 
                                      'attachment_id', 'Attachments')
    price_total = fields.Float( string='Total',
                                track_visibility='onchange', 
                                compute="_compute_amount",
                                store=True)
    is_accepted = fields.Boolean(string="Is accepted",
                                 compute="_compute_is_accepted",
                                 readonly=True)
    
    
    
    is_warehouse_notes = fields.Boolean(string="Is Warehouse Notes",
                                 compute="_compute_is_warehouse_notes",
                                 readonly=True)
    
    is_usr = fields.Boolean(string="Is Requested by User",
                                 compute="_compute_is_usr",
                                 readonly=True)
    
    warehouse_manager_notes = fields.Text('Warehouse manager notes')
    
    budget_id = fields.Many2one('crossovered.budget' , string='Budget', required=True)
    budget_drc = fields.Many2one('account.budget.post', string="DRC", required=True)
    budget_dea = fields.Many2one('crossovered.budget.lines', string='DEA', required=True)
    total_dea = fields.Float(related='budget_dea.planned_amount', string="DEA Amount")
    
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
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
               
    def _compute_is_warehouse_notes(self):
        for rec in self:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_82'):
                    rec.is_warehouse_notes = True
                else:
                    rec.is_warehouse_notes= False
    
          
    def _compute_is_usr(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_usr = True
            else:
                rec.is_usr = False
                    

    @api.one
    @api.depends('product_qty', 'product_price')
    def _compute_amount(self):
        if self.product_qty > 0:
            self.price_total = self.product_price * self.product_qty

    