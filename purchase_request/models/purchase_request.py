# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models
import urlparse, os
import datetime
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp

_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'Assigne Direct Manager'),
    ('to_department_manager_approved', 'Assigne Department Manager'),
    ('to_accountant_manager_approved', 'Assigne CFO Manager'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
]

_STAGES = [
    (1, 'Purchase Request'),
    (2, 'Direct And Department Managers Approve'),
    (3, 'ًWarehouse'),
    (4, 'CFO Approve'),
    (5, 'Specify Request Price'),
    (6, 'Processing Quotations'),
    (7, 'Technical Specification'),
    (8, 'CEO Approve'),
    (9, 'Processing of the Financial Note'),
    (10, 'Treasurer Approve'),
    (11, 'Chairman Approve'),
    (12, 'Check Payment'),
    (13, 'Purchase Order'),
    (14, 'Delivery Request'),
    (15, 'Reject')
]

_STEPS = [
    (1, 'Specify Technical Specification'),
    (2, 'Conditions booklet'),
    (3, 'Legal Counsel Review'),
    (4, 'CFO Review'),
    (5, 'Receipt of the approved conditions booklet'),
    (6, 'Advertising in newspapers'),
    (7, 'Receiving supplier RFQs'),
    (8, 'Determination of the commission of the RFQs'),
    (9, 'Opening the booklets and marking on the supplier')
]

_TYPES = [
    (1, 'Normal'),
    (2, 'Urgent'),
    (3, 'Exception')
]

_WAREHOUSES = [
    (1, 'Available in Warehouse'),
    (2, 'Not Available in Warehouse')
]

class PurchaseRequest(models.Model):

    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _company_get(self):
        company_id = self.env['res.company']._company_default_get(self._name)
        return self.env['res.company'].browse(company_id.id)

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('purchase.request')

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
            if rec.state in ('to_approve', 'to_department_manager_approved','to_accountant_manager_approved','approved', 'rejected'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.multi
    def _track_subtype(self, init_values):
        for rec in self:
            if 'state' in init_values and rec.state == 'to_approve':
                return 'purchase_request.mt_request_to_approve'
            elif 'state' in init_values and rec.state == 'to_department_manager_approved':
                return 'purchase_request.mt_request_to_department_manager_approved'
            elif 'state' in init_values and rec.state == 'to_accountant_manager_approved':
                return 'purchase_request.mt_request_to_accountant_manager_approved'
            elif 'state' in init_values and rec.state == 'approved':
                return 'purchase_request.mt_request_approved'
            elif 'state' in init_values and rec.state == 'rejected':
                return 'purchase_request.mt_request_rejected'
        return super(PurchaseRequest, self)._track_subtype(init_values)
    
    @api.onchange('stock_warehouse')
    def onchange_stock(self):
        if self.stock_warehouse == 1:
            self.stage = 14
        elif self.stock_warehouse == 2:
            self.stage = 4

    name = fields.Char('Request Reference', size=32, required=True,
                       default=_get_default_name,
                       track_visibility='onchange')
    origin = fields.Char('Source Document', size=32, compute=_get_default_origin)
    reject_reason = fields.Char('reject_reason', default=' ')
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the"
                                  "request.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')
    date_finish = fields.Date('Expected date',
                             help="Date when the Request will"
                                  "Finish.",
                             default=fields.Date.context_today,
                             compute='_check_the_date',
                             track_visibility='onchange')
    requested_by = fields.Many2one('res.users',
                                   'Requested by',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    assigned_to = fields.Many2one('res.users', 'Department Managers',
                                  domain=[('x_department_manager', '=', True)],
                                  track_visibility='onchange')
    assigned_to_2 = fields.Many2one('res.users', 'Department Managers',
                                  domain=[('x_department_manager', '=', True)],
                                  track_visibility='onchange')
    assigned_to_3 = fields.Many2one('res.users', 'Projects/Sections Managers',
                                  domain=[('x_project_manager', '=', True)],
                                  track_visibility='onchange')
    description = fields.Text('Description')
    direct_manager_notes = fields.Text('Direct manager notes')
    department_manager_notes = fields.Text('Department manager notes')
    purchase_manager_notes = fields.Text('Purchases manager notes')
    warehouse_manager_notes = fields.Text('Warehouse manager notes')
    accountant_manager_notes = fields.Text('CFO notes')
    executive_manager_notes = fields.Text('Executive manager notes')
    treasurer_manager_notes = fields.Text('Treasurer notes')
    president_manager_notes = fields.Text('Chairman notes')
    company_id = fields.Many2one('res.company', 'Company',
                                 required=True,
                                 default=_company_get,
                                 track_visibility='onchange')
    line_ids = fields.One2many('purchase.request.line', 'request_id',
                               'Products to Purchase',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')
    stage = fields.Selection(selection=_STAGES,
                             default=1,
                             string='Stage')
    stock_warehouse = fields.Selection(selection=_WAREHOUSES,
                             string='Stock',on_change="onchange_stock(stock_warehouse)")
    #stock_warehouse = fields.ٍSelection(selection=_WAREHOUSES,string='Stock')
    steps = fields.Selection(selection=_STEPS,
                            string='Technical Specifications Steps')
    request_type = fields.Selection(selection=_TYPES,
                                    default=1,
                                    help = 'Provide request as soon as possible :عاجل',
                                    string='Request Type')
    
    type_reason = fields.Text('Reason')
    explain_type = fields.Char('Explain',compute='_compute_explain')
    department = fields.Many2one('hr.department', 'Department',
                                  track_visibility='onchange')
    project = fields.Many2one('hr.department', 'Project/Section',
                                  track_visibility='onchange')
    is_editable = fields.Boolean(string="Is editable",
                                 compute="_compute_is_editable",
                                 readonly=True)

    picking_type_id = fields.Many2one('stock.picking.type',
                                      'Picking Type', required=True,
                                      default=_default_picking_type)

    ontime = fields.Integer(string='On Time',
                            compute="change_ontime",
                            readonly=True)
    ontime_stage = fields.Integer(string='On Time Stage',
                            compute="change_ontime_stage",
                            readonly=True)
    done1= fields.Char(string='Done',
                       compute="change_done_stage",
                       default='early')
    progress = fields.Float(string='Progress',
                          compute='change_progress',
                          readonly=True)
    color = fields.Integer('Color Index',
                           compute="change_colore_on_kanban")
    
    price_alltotal = fields.Float( string='Total Price', compute='_compute_amount_all', store=True)
    is_direct_notes = fields.Boolean(string="Is Direct Notes",
                                 compute="_compute_is_direct_notes",
                                 readonly=True)
    is_dept_notes = fields.Boolean(string="Is Dept Notes",
                                 compute="_compute_is_dept_notes",
                                 readonly=True)
    is_purchase_notes = fields.Boolean(string="Is Purchase Notes",
                                 compute="_compute_is_purchase_notes",
                                 readonly=True)
    is_warehouse_notes = fields.Boolean(string="Is Warehouse Notes",
                                 compute="_compute_is_warehouse_notes",
                                 readonly=True)
    is_account_notes = fields.Boolean(string="Is Accountant Notes",
                                 compute="_compute_is_account_notes",
                                 readonly=True)
    is_treasure_notes = fields.Boolean(string="Is Treasure Notes",
                                 compute="_compute_is_treasure_notes",
                                 readonly=True)
    is_pres_notes = fields.Boolean(string="Is pres Notes",
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
        
    @api.multi
    @api.depends('requested_by')    
    def _compute_is_request_approval(self):
        for rec in self:
            #dep_mang = self.env['res.users'].browse(['res.users'].x_department_manager)
            usr = self.env['res.users'].browse(self.env.uid)
            if usr == rec.requested_by and rec.state == 'draft':
                rec.is_request_approval = True
            elif usr == rec.requested_by and rec.state != 'draft':
                rec.is_request_approval = False
            elif usr != rec.requested_by and rec.state == 'draft':
                rec.is_request_approval = False
            elif usr != rec.requested_by and rec.state != 'draft':
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
    def _compute_is_purchase_notes(self):
        for rec in self:
            if rec.requested_by == self.env['res.users'].browse(self.env.uid):
                rec.is_purchase_notes = True
            else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_56'):
                    rec.is_purchase_notes = True
                else:
                    rec.is_purchase_notes= False
    @api.multi
    @api.depends('requested_by')                
    def _compute_is_warehouse_notes(self):
        for rec in self:
            #if rec.requested_by == self.env['res.users'].browse(self.env.uid):
             #   rec.is_warehouse_notes = True
            #else:
                user = self.env['res.users'].browse(self.env.uid)
                if user.has_group('__export__.res_groups_82'):
                    rec.is_warehouse_notes = True
                else:
                    rec.is_warehouse_notes= False
    
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
    @api.depends('line_ids.price_total')
    def _compute_amount_all(self):
        for request in self:
            for line in request.line_ids: 
                request.price_alltotal += line.price_total
            #if request.price_alltotal > 0:
             #   request.stage = 5
    
    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'draft',
            'name': self.env['ir.sequence'].get('purchase.request'),
        })
        return super(PurchaseRequest, self).copy(default)

    @api.model
    def create(self, vals):
        request = super(PurchaseRequest, self).create(vals)
        if vals.get('assigned_to'):
            request.message_subscribe_users(user_ids=[request.assigned_to.id])
        return request

    @api.multi
    def write(self, vals):
        res = super(PurchaseRequest, self).write(vals)
        for request in self:
            if vals.get('assigned_to'):
                self.message_subscribe_users(user_ids=[request.assigned_to.id])
        return res

    @api.multi
    def button_draft(self):
        for rec in self:
            #rec.state = 'draft'
            #rec.stage = 1
            
            if self.state == 'to_approve' and self.direct_manager_notes != False:
                rec.state = 'draft'
                rec.stage = 1
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 'to_department_manager_approved' and self.department_manager_notes != False:
                rec.state = 'draft'
                rec.stage = 1
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 'to_accountant_manager_approved' and self.accountant_manager_notes != False:
                rec.state = 'draft'
                rec.stage = 1
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 'approved' and self.accountant_manager_notes != False:
                rec.state = 'draft'
                rec.stage = 1
                rec.is_reject_required = False
            elif self.state == 'rejected' and self.accountant_manager_notes != False:
                rec.state = 'draft'
                rec.stage = 1
                rec.is_reject_required = False
            else:
                if self.state == 'to_approve':
                    rec.reject_reason = 'You Could Write Reject Reason In direct manager notes'
                    rec.is_reject_required = True
                elif self.state == 'to_department_manager_approved':
                    rec.reject_reason = 'You Could Write Reject Reason In department manager notes'
                    rec.is_reject_required = True
                elif self.state == 'to_accountant_manager_approved':
                    rec.reject_reason = 'You Could Write Reject Reason In CFO manager notes'
                    rec.is_reject_required = True
                elif self.state == 'approved':
                    rec.reject_reason = 'You Could Write Reject Reason In CFO manager notes'
                    rec.is_reject_required = True
                elif self.state == 'rejected':
                    rec.reject_reason = 'You Could Write Reject Reason In CFO manager notes'
                    rec.is_reject_required = True
        return True

    @api.multi
    def button_to_approve(self):
        for rec in self:
            if rec.assigned_to_3:
                rec.state = 'to_approve'
                rec.stage = 2
            elif rec.assigned_to_3 == 0:
                rec.state = 'to_department_manager_approved'
                rec.stage = 2
            else:
                if rec.assigned_to:
                    rec.state = 'to_department_manager_approved'
                    rec.stage = 2
                elif rec.assigned_to == 0:
                    rec.state = 'to_accountant_manager_approved'
                    rec.stage = 4
                else:
                    rec.state = 'to_accountant_manager_approved'
                    rec.stage = 4
        return True
    
    @api.multi
    def button_to_department_manager_approved(self):
        for rec in self:
            rec.state = 'to_department_manager_approved'
        return True

    @api.multi
    def button_to_accountant_manager_approved(self):
        for rec in self:
            rec.state = 'to_accountant_manager_approved'
            rec.stage = 3
        return True
    
    @api.multi
    def button_approved(self):
        for rec in self:
            rec.state = 'approved'
            rec.stage = 5
        return True

    @api.multi
    def button_rejected(self):
        for rec in self:
             
            if self.state == 'to_approve' and self.direct_manager_notes != False:
                rec.state = 'rejected'
                rec.stage = 15
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 'to_department_manager_approved' and self.department_manager_notes != False:
                rec.state = 'rejected'
                rec.stage = 15
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 'to_accountant_manager_approved' and self.accountant_manager_notes != False:
                rec.state = 'rejected'
                rec.stage = 15
                rec.is_reject_required = False
                #raise ValidationError("You can reject request after write reason in notes:")
                #return False
            elif self.state == 'approved' and self.accountant_manager_notes != False:
                rec.state = 'rejected'
                rec.stage = 15
                rec.is_reject_required = False
            else:
                if self.state == 'to_approve':
                    rec.reject_reason = 'You Could Write Reject Reason In direct manager notes'
                    rec.is_reject_required = True
                elif self.state == 'to_department_manager_approved':
                    rec.reject_reason = 'You Could Write Reject Reason In department manager notes'
                    rec.is_reject_required = True
                elif self.state == 'to_accountant_manager_approved':
                    rec.reject_reason = 'You Could Write Reject Reason In CFO manager notes'
                    rec.is_reject_required = True
                elif self.state == 'approved':
                    rec.reject_reason = 'You Could Write Reject Reason In CFO manager notes'
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
            if rec.price_alltotal <= 500 and rec.price_alltotal > 0 and (rec.state == 'to_accountant_manager_approved' or rec.state == 'approved'):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=6)
                rec.date_finish = new_date
            elif rec.price_alltotal > 500 and rec.price_alltotal <= 5000 and (rec.state == 'to_accountant_manager_approved' or rec.state == 'approved'):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=6)
                rec.date_finish = new_date
            elif rec.price_alltotal > 5000 and rec.price_alltotal <= 100000 and (rec.state == 'to_accountant_manager_approved' or rec.state == 'approved'):
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=12)
                rec.date_finish = new_date
            elif rec.price_alltotal > 100000 and (rec.state == 'to_accountant_manager_approved' or rec.state == 'approved'):
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
    
    def change_ontime(self):
        for rec in self:
            if rec.stage == 14 or rec.stage == 15:
                rec.ontime = rec.ontime
            else:
                if rec.state == 'approved':
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
                    if record.state == 'to_accountant_manager_approved':
                        color = 3
                    elif record.state == 'to_department_manager_approved':
                        color = 3
                    elif record.state == 'rejected':
                        color = 6
                    else:
                        color = 3
                elif record.ontime > 0:
                    color = 5
                elif record.progress == 100:
                    color = 5
                elif record.state == 'rejected':
                    color = 1
            record.color = color
            
    @api.multi
    def write(self,vals):
        # Your logic goes here or call your method
        super(PurchaseRequest, self).write(vals)
        for ss in self:
            if ss.state == 'rejected':
                ss.env.cr.execute("UPDATE purchase_request SET stage = 15 WHERE id = '%s' " %(ss.id))
        return True    
    
class PurchaseRequestLine(models.Model):

    _name = "purchase.request.line"
    _description = "Purchase Request Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'analytic_account_id', 'date_required', 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_approve', 'to_department_manager_approved','to_accountant_manager_approved','approved', 'rejected'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.multi
    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.seller_ids:
                    rec.supplier_id = rec.product_id.seller_ids[0].name

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('purchase_ok', '=', True)],
        track_visibility='onchange')
    name = fields.Char('Description', size=256, required=True, 
                       track_visibility='onchange')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',
                                     track_visibility='onchange')
    product_qty = fields.Float('Quantity', track_visibility='onchange', default = 1,
                               digits_compute=dp.get_precision(
                                   'Product Unit of Measure'))
    product_price = fields.Float('Price', track_visibility='onchange')
    accepted = fields.Boolean('Accepted', track_visibility='onchange')
    request_id = fields.Many2one('purchase.request',
                                 'Purchase Request',
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
    date_required = fields.Date(string='Request Date', required=True,
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
    
    stock_warehouse = fields.Selection(selection=_WAREHOUSES,
                             string='Stock')
    
    is_warehouse_notes = fields.Boolean(string="Is Warehouse Notes",
                                 compute="_compute_is_warehouse_notes",
                                 readonly=True)
    
    is_usr = fields.Boolean(string="Is Requested by User",
                                 compute="_compute_is_usr",
                                 readonly=True)
    
    warehouse_manager_notes = fields.Text('Warehouse manager notes')
    
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
            #name = self.product_id.name
            #if self.product_id.code:
             #   name = '[%s] %s' % (name, self.product_id.code)
            #if self.product_id.description_purchase:
             #   name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            #self.product_qty = 1
            #self.name = name
               
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
