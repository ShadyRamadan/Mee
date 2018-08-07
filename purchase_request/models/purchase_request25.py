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
    ('to_accountant_manager_approved', 'Assigne Accountant Manager'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
]

_STAGES = [
    (1, 'تقديم الطلب'),
    (2, 'موافقة مدير القسم ومدير الإدارة'),
    (3, 'متوفر بالمخازن'),
    (4, 'غير متوفر بالمخازن'),
    (5, 'تحديد قيمة الطلب'),
    (6, 'موافقة الإدارة المالية'),
    (7, 'تجهيز عروض اﻷسعار'),
    (8, 'المواصفات الفنية'),
    (9, 'موافقة المدير التنفيذي'),
    (10, 'تجهيز المذكرة المالية'),
    (11, 'موافقة أمين الصندوق وإمضاء الشيك'),
    (12, 'موافقة رئيس مجلس اﻷمناء أو نائبه'),
    (13, 'صرف الشيك'),
    (14, 'شراء المنتج وتسليمه للموظف')
]

_STEPS = [
    (1, 'تحديد المواصفات الفنية للطلب'),
    (2, 'كراسة الشروط'),
    (3, 'مراجعة المستشار القانوني'),
    (4, 'مراجعة الإدارة المالية'),
    (5, 'إستلام كراسة الشروط المعتمدة'),
    (6, 'الإعلان في الصحف'),
    (7, 'إستلام عروض الموردين'),
    (8, 'تحديد لجنة بت الطلبات'),
    (9, 'فتح الكراسات والترسية على المورد')
]

_TYPES = [
    (1, 'عادي'),
    (2, 'عاجل'),
    (3, 'استثنائي')
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
            if rec.state in ('to_approve', 'approved', 'rejected'):
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

    name = fields.Char('Request Reference', size=32, required=True,
                       default=_get_default_name,
                       track_visibility='onchange')
    origin = fields.Char('Source Document', size=32)
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the "
                                  "request.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')
    date_finish = fields.Date('Expected date',
                             help="Date when the Request will  "
                                  "Finish.",
                             default=fields.Date.context_today,
                             compute='_check_the_date',
                             track_visibility='onchange')
    requested_by = fields.Many2one('res.users',
                                   'Requested by',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    assigned_to = fields.Many2one('res.users', 'Approver',
                                  track_visibility='onchange')
    assigned_to_2 = fields.Many2one('res.users', 'Department Managers',
                                  domain=[('x_department_manager', '=', True)],
                                  track_visibility='onchange')
    assigned_to_3 = fields.Many2one('res.users', 'Projects or Sections Managers',
                                  domain=[('x_project_manager', '=', True)],
                                  track_visibility='onchange')
    description = fields.Text('Description')
    direct_manager_notes = fields.Text('Direct manager notes')
    department_manager_notes = fields.Text('Department manager notes')
    accountant_manager_notes = fields.Text('Accountant manager notes')
    treasurer_manager_notes = fields.Text('Treasurer manager notes')
    president_manager_notes = fields.Text('President manager notes')
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
    steps = fields.Selection(selection=_STEPS,
                            string='Technical Specifications Steps')
    request_type = fields.Selection(selection=_TYPES,
                                    default=1,
                                    string='Request Type')
    type_reason = fields.Text('Reason')

    department = fields.Many2one('hr.department', 'Department',
                                  track_visibility='onchange')
    project = fields.Many2one('hr.department', 'Project',
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
                       default='early')
    progress = fields.Float(string='Progress',
                          compute='change_progress',
                          readonly=True)
    color = fields.Integer('Color Index',
                           compute="change_colore_on_kanban")
    price_alltotal = fields.Float( string='Total Price', compute='_compute_amount_all', store=True)

    @api.multi
    @api.depends('line_ids.price_total')
    def _compute_amount_all(self):
        for request in self:
            for line in request.line_ids: 
                request.price_alltotal += line.price_total
            if request.price_alltotal > 0:
                request.stage = 5
    
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
            rec.state = 'draft'
        return True

    @api.multi
    def button_to_approve(self):
        for rec in self:
            rec.state = 'to_approve'
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
            rec.stage = 2
        return True
    
    @api.multi
    def button_approved(self):
        for rec in self:
            rec.state = 'approved'
            rec.stage = 6
        return True

    @api.multi
    def button_rejected(self):
        for rec in self:
            rec.state = 'rejected'
        return True

    @api.multi
    def _check_the_date(self):
        #for rec in self:
         #   d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
          #  new_date = d1 + datetime.timedelta(days=18)
           # rec.date_finish = new_date
        for rec in self:
            if rec.price_alltotal <= 500:
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=4)
                rec.date_finish = new_date
            elif rec.price_alltotal > 500 and rec.price_alltotal <= 5000:
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=5)
                rec.date_finish = new_date
            elif rec.price_alltotal > 5000 and rec.price_alltotal <= 100000:
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=7)
                rec.date_finish = new_date
            elif rec.price_alltotal > 100000:
                d1 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
                new_date = d1 + datetime.timedelta(days=15)
                rec.date_finish = new_date

    def change_progress(self):
        for rec in self:
            x = rec.stage 
            y = x * 100 / 14
            rec.progress= y
    
    def change_ontime(self):
        for rec in self:
            d1 = datetime.datetime.today()
            d2 = datetime.datetime.strptime((rec.date_finish),'%Y-%m-%d') 
            d = str((d2-d1).days + 1)
            rec.ontime = d
    def change_ontime_stage(self):
        for rec in self:
            d1 = datetime.datetime.today()
            d2 = datetime.datetime.strptime((rec.date_start),'%Y-%m-%d') 
            d = str((d1-d2).days + 1)
            rec.ontime_stage = d

    def change_colore_on_kanban(self):   
        for record in self:
            color = 0
            if record.ontime < 0:
                color = 2
            elif record.ontime == 0:
                color = 3
            elif record.ontime > 0:
                color = 5
            record.color = color
                       
class PurchaseRequestLine(models.Model):

    _name = "purchase.request.line"
    _description = "Purchase Request Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'analytic_account_id', 'date_required', 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_approve', 'approved', 'rejected'):
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
    name = fields.Char('Description', size=256,
                       track_visibility='onchange')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',
                                     track_visibility='onchange')
    product_qty = fields.Float('Quantity', track_visibility='onchange',
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
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name

    @api.multi
    @api.depends('product_qty', 'product_price')
    def _compute_amount(self):
        if self.product_qty > 0:
            self.price_total = self.product_price * self.product_qty
