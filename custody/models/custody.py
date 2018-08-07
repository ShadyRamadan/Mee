# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models
import urlparse, os
import datetime
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp


_STATES = [
    (1, 'Draft'),
    (2, 'Delivery'),
    (3, 'Receipt')
]

class custody(models.Model):
    
    _name = 'warehouse.custody'
    _description = 'Warehouse Custody'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)
    
    @api.onchange('employee_user')
    def _onchange_allowed_purchase_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders.
        '''
        result = {}
        # A PO can be selected only if at least one PO line is not already in the invoice
        #purchase_line_ids = self.line_ids.mapped('purchase_request_line_id')
        #purchase_ids = self.line_ids.mapped('purchase_request_id').filtered(lambda r: r.line_ids <= purchase_line_ids)
        result['domain'] = {'purchase_request': [
            ('requested_by', '=', self.employee_user.id),
            ('stage', '=', 14)
            ]}
        return result
    #('id', 'not in', purchase_ids.ids),
    @api.onchange('purchase_request')
    def onchange_purchase(self):
        self.department = self.purchase_request.department
        self.project = self.purchase_request.project
        
    state = fields.Selection(selection=_STATES,string='Status',index=True,
                             track_visibility='onchange',required=True,copy=False,
                             default=1)
    custody_number = fields.Char('Custody Number')
    color = fields.Integer('Color Index',compute="change_colore_on_kanban")
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True,
                                   track_visibility='onchange')
    employee_user = fields.Many2one(related='employee_id.user_id',
                                 string='Employee User',
                                 store=True, readonly=True) 
    requested_by = fields.Many2one('res.users','Written by', required=True,
                                   track_visibility='onchange', readonly=True,
                                   default=_get_default_requested_by)
    delivery_date = fields.Date('Delivery date', 
                                default=fields.Date.context_today,
                             help="Date when the user delivered the custody.",
                             track_visibility='onchange')
    finish_date = fields.Date('Finish date', track_visibility='onchange',
                             help="Date when the Custody will Finish.")
    is_active = fields.Boolean('Active')
    department = fields.Many2one('hr.department', 'Department',
                                 track_visibility='onchange')
    project = fields.Many2one('hr.department', 'Project/Section',
                                  track_visibility='onchange')
    purchase_request = fields.Many2one('purchase.request', 'Purchase Request' 
                                       ,track_visibility='onchange'
                            ,on_change="onchange_purchase(purchase_request)")
    purchase_request_date = fields.Date(related='purchase_request.date_start',
                                 string='Request Date',
                                 store=True, readonly=True)
    
    line_ids = fields.One2many('warehouse.custody.line', 'custody_id',
                               'Products to Custody', readonly=False, copy=True,
                               track_visibility='onchange')
    
    def _prepare_custody_line_from_pu_line(self, line):
        #if line.product_id.purchase_method == 'purchase':
         #   qty = line.product_qty - line.qty_invoiced
        #else:
         #   qty = line.qty_received - line.qty_invoiced
        #if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
         #   qty = 0.0
        #taxes = line.taxes_id
        #invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
        custody_line = self.env['warehouse.custody.line']
        data = {
            'purchase_request_line_id': line.id,
            'name': line.name,
            #'origin': self.purchase_id.origin,
            #'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            #'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            #'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id, round=False),
            'quantity': line.product_qty,
            #'discount': 0.0,
            #'account_analytic_id': line.account_analytic_id.id,
            #'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        #account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
        #if account:
         #   data['account_id'] = account.id
        return data

    # Load all unsold PO lines
    @api.onchange('purchase_request')
    def purchase_request_change(self):
        if not self.purchase_request:
            return {}
        #if not self.partner_id:
         #   self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['warehouse.custody.line']
        for line in self.purchase_request.line_ids:
            data = self._prepare_custody_line_from_pu_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.line_ids += new_lines
        #self.purchase_request = False
        return {}
    
    @api.multi
    def button_reset(self):
        for rec in self:
            rec.state = 1
            rec.delivery_date = False
            rec.finish_date = False
            rec.is_active = False
        return True
    
    @api.multi
    def button_receipt(self):
        for rec in self:
            rec.state = 3
            rec.finish_date = datetime.datetime.today()
            rec.is_active = False
        return True
    
    @api.multi
    def button_delivery(self):
        for rec in self:
            rec.state = 2
            rec.delivery_date= datetime.datetime.today()
            rec.is_active = True
        return True
    
    def change_colore_on_kanban(self):   
        for record in self:
            if record.state == 1:
                record.color = 3
            elif record.state == 2:
                record.color = 5
            elif record.state == 3:
                record.color = 6
    
class custody_line(models.Model):
    _name = 'warehouse.custody.line'
    _description = 'Warehouse Custody Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
        
    custody_id = fields.Many2one('warehouse.custody',
                                 string='Custody',
                                 ondelete='cascade', readonly=True)
    name = fields.Char('Item')
    product_id = fields.Many2one('product.product', 'Product',
                domain=[('purchase_ok', '=', True)],track_visibility='onchange')
    product_qty = fields.Float('Quantity', track_visibility='onchange',
                                    default = 1)
        
    requested_by = fields.Many2one('res.users',
                                   related='custody_id.requested_by',
                                   string='Requested by',
                                   store=True, readonly=True)
    date_start = fields.Date(related='custody_id.delivery_date',
                             string='Delivery Date', readonly=True, store=True)
    employee_id = fields.Many2one('hr.employee', string ='Employee',
                                   related='custody_id.employee_id',
                                   required=True, track_visibility='onchange')
    finish_date = fields.Date(related='custody_id.finish_date', 
                              string = 'Finish date',
                              help="Date when the Custody will Finish.",
                              track_visibility='onchange')
    is_active = fields.Boolean(related='custody_id.is_active', string = 'Active')
    is_warranty = fields.Boolean('Warranty')
    #warranty_from = fields.Date(
        #related='product_id.finish_date', 
     #                        string = 'Warranty date from',
      #                       help="Date when the product warranty start.",
       #                      track_visibility='onchange')
    #warranty_to = fields.Date(
        #related='product_id.finish_date', 
     #                         string='Warranty date To',
      #                        help="Date when the product warranty finish.",
       #                   track_visibility='onchange')
    internal_reference = fields.Char(related='product_id.default_code',
                                     string='Internal Reference',store=True)
    barcode = fields.Char(related='product_id.barcode',
                                     string='Barcode',store=True)
    description =fields.Text(related='product_id.description_sale',
                                     string='Description',store=True)
    #location = fields.Many2one()
    purchase_request_line_id = fields.Many2one('purchase.request.line', 'Purchase Request Line', ondelete='set null', index=True, readonly=True)
    purchase_request_id = fields.Many2one('purchase.request', related='purchase_request_line_id.request_id', string='Purchase Request', store=False, readonly=True, related_sudo=False,
        help='Associated Purchase Request. Filled in automatically when a PU is chosen on the vendor bill.')
    
    
    def _set_additional_fields(self, invoice):
        """ Some modules, such as Purchase, provide a feature to add automatically pre-filled
            invoice lines. However, these modules might not be aware of extra fields which are
            added by extensions of the accounting module.
            This method is intended to be overridden by these extensions, so that any new field can
            easily be auto-filled as well.
            :param invoice : account.invoice corresponding record
            :rtype line : account.invoice.line record
        """
        pass