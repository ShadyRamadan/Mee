# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models , _
import urlparse, os
import datetime
from openerp.exceptions import UserError, ValidationError
from openerp.tools import float_is_zero, float_compare
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp

_STATES = [
    (1, 'Draft'),
    (2, 'Validate'),
    #(3, 'Posted'),
    #(4, 'Bank')
]

class OtherIncome(models.Model):
    _name = 'other.income'
    _description = 'Other Incomes'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    @api.model
    def _company_get(self):
        company_id = self.env['res.company']._company_default_get(self._name)
        return self.env['res.company'].browse(company_id.id)

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)
    
    @api.model
    @api.depends('income_type')
    def _get_default_name(self):
        for income in self:
            if isinstance(income.id, models.NewId):
                income.name = income.income_type.name
            else:   
                income.name = income.income_type.name   
                         
    @api.model
    def _get_default_origin(self):
        for rec in self:
            rec.origin = rec.name
            
    @api.model
    def _default_currency(self):
        company = self.env['res.company']._company_default_get(
            'otherr.income')
        return company.currency_id
    
    @api.multi
    @api.depends(
        'line_ids', 'line_ids.unit_price', 'line_ids.quantity',
        'income_date', 'currency_id', 'company_id')
    def _compute_total(self):
        for income in self:
            total = tax_receipt_total = 0.0
            company_currency = income.company_currency_id
            income_currency = income.currency_id
            # Do not consider other currencies for tax receipts
            # because, for the moment, only very very few countries
            # accept tax receipts from other countries, and never in another
            # currency. If you know such cases, please tell us and we will
            # update the code of this module
            for line in income.line_ids:
                #line_total = line.quantity * line.unit_price
                line_total = line.amount
                total += line_total

            income.amount_total = total
            #income_currency =\
             #   income.currency_id.with_context(date=income.income_date)
            #total_company_currency = income_currency.compute(
             #   total, income.company_id.currency_id)
            #income.amount_total_company_currency = total_company_currency
    
    name = fields.Char('Income Reference', size=32,
                       compute=_get_default_name,track_visibility='onchange')
    income_date = fields.Date('Date',default=fields.Date.context_today,
                             track_visibility='onchange',
                             help="Date when the user initiated the request.")
    responsible_by = fields.Many2one('res.users','User',required=True,
                                   track_visibility='onchange',default=_get_default_requested_by)
    company_id = fields.Many2one('res.company', 'Company',required=True,
                                 default=_company_get, track_visibility='onchange')
    state = fields.Selection(selection=_STATES,string='Status',index=True,
                             track_visibility='onchange',copy=False,default=1)
    income_type = fields.Many2one('income.type','Income Type',store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
        states={3: [('readonly', True)]},
        track_visibility='onchange', ondelete='restrict',default=_default_currency)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string="Company Currency",
        readonly=True)
    line_ids = fields.One2many(
        'income.line', 'income_id', string='Income Lines', copy=True)
    move_id = fields.Many2one(
        'account.move', string='Account Move', readonly=True, copy=False)
    type_account = fields.Many2one ('account.account', related='income_type.account_id', string='Type Account')
    amount_total = fields.Monetary(compute='_compute_total', string='Amount Total',
        currency_field='currency_id', store=True, readonly=True,digits=dp.get_precision('Account'))
    
    
    @api.model
    def _prepare_move_line_name(self):
        name = _('Income of %s') % self.income_type.name
        return name
    
    @api.multi
    def _prepare_counterpart_move_line(self, name, amount_total_company_cur, total_amount_currency,currency_id):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Account')
        if float_compare(amount_total_company_cur, 0, precision_digits=precision) == 1:
            #debit = amount_total_company_cur
            #credit = 0
            #total_amount_currency = self.amount_total
            credit = amount_total_company_cur
            debit = 0
            total_amount_currency = self.amount_total
        else:
            debit= amount_total_company_cur * -1
            credit = 0
            total_amount_currency = self.amount_total * -1
            #credit = amount_total_company_cur * -1
            #debit = 0
            #total_amount_currency = self.amount_total * -1
        vals = {
            'debit': debit,
            'credit': credit,
            'name': name,
            #'account_id': self.journal_id.default_debit_account_id.id,
            'account_id': self.type_account.id,
            #'partner_id': '',
            'currency_id': currency_id,
            'amount_currency': (currency_id and total_amount_currency or 0.0),
            }
        return vals

    @api.multi
    def _prepare_donation_move(self):
        self.ensure_one()
        if not self.income_type.account_id.id:
            raise UserError(
                _("Missing Default Credit Account on Income Type '%s'.")
                % self.income_type.name)

        movelines = []
        if self.company_id.currency_id.id != self.currency_id.id:
            currency_id = self.currency_id.id
        else:
            currency_id = False
        # Note : we can have negative donations for donors that use direct
        # debit when their direct debit rejected by the bank
        amount_total_company_cur = 0.0
        total_amount_currency = 0.0
        name = self._prepare_move_line_name()
        aml = {}
        # key = (account_id, analytic_account_id)
        # value = {'credit': ..., 'debit': ..., 'amount_currency': ...}
        precision = self.env['decimal.precision'].precision_get('Account')
        for income_line in self.line_ids:
            #if income_line.in_kind:
             #   continue
            amount_total_company_cur += income_line.amount
            #account_id = donation_line.product_id.property_account_income_id.id
            #if not account_id:
             #   account_id = donation_line.product_id.categ_id.\
              #      property_account_income_categ_id.id
            account_id = income_line.get_account_id()
            if not account_id:
                raise UserError(
                    _("Missing income account on method '%s'")
                    % income_line.payment_method.name)
            analytic_account_id = income_line.get_analytic_account_id()
            
            amount_currency = 0.0
            if float_compare(
                    income_line.amount, 0,
                    precision_digits=precision) == 1:
                #credit = donation_line.amount_company_currency
                #debit = 0
                #amount_currency = donation_line.amount * -1
                debit= income_line.amount
                credit = 0
                amount_currency = income_line.amount * -1
            else:
                #debit = donation_line.amount_company_currency * -1
                #credit = 0
                #amount_currency = donation_line.amount
                credit = income_line.amount * -1
                debit = 0
                amount_currency = income_line.amount

            # TODO Take into account the option group_invoice_lines ?
            if (account_id, analytic_account_id) in aml:
                aml[(account_id, analytic_account_id)]['credit'] += credit
                aml[(account_id, analytic_account_id)]['debit'] += debit
                aml[(account_id, analytic_account_id)]['amount_currency'] \
                    += amount_currency
            else:
                aml[(account_id, analytic_account_id)] = {
                    'credit': credit,
                    'debit': debit,
                    'amount_currency': amount_currency,
                    }

        if not aml:  # for full in-kind donation
            return False

        for (account_id, analytic_account_id), content in aml.iteritems():
            movelines.append((0, 0, {
                'name': name,
                'credit': content['credit'],
                'debit': content['debit'],
                'account_id': account_id,
                'analytic_account_id': analytic_account_id,
                #'partner_id': self.commercial_partner_id.id,
                'currency_id': currency_id,
                'amount_currency': (
                    currency_id and content['amount_currency'] or 0.0),
                }))

        # counter-part
        ml_vals = self._prepare_counterpart_move_line(
            name, amount_total_company_cur, total_amount_currency,currency_id)
        movelines.append((0, 0, ml_vals))

        vals = {
            'journal_id': self.income_type.journal_id.id,
            'date': self.income_date,
            'ref': self.name,
            'line_ids': movelines,
            }
        return vals
    
    @api.one
    def _prepare_analytic_line(self):
        """ Prepare the values used to create() an account.analytic.line upon validation of an account.move.line having
            an analytic account. This method is intended to be extended in other modules.
        """
        tags_id=[]
        #for donation_line in self.line_ids:
            #if donation_line.in_kind:
                #continue
        #amount = (self.credit or 0.0) - (self.debit or 0.0)
        #account_id = self.line_ids.product_id.property_account_income_id.id
        for donation_line in self.line_ids:
            account_id = donation_line.get_account_id()
            analytic_account_id = donation_line.get_analytic_account_id()
            #tags_id = donation_line.tags_id
            
        #if not account_id:
         #   account_id = self.line_ids.product_id.categ_id.property_account_income_categ_id.id    
        name = self._prepare_move_line_name()
        vals = {
            'name': name,
            'date': self.income_date,
            'account_id': analytic_account_id,
            #'partner_id': self.commercial_partner_id.id,
            #'unit_amount': self.quantity,
            #'product_id': self.product_id and self.product_id.id or False,
            #'product_uom_id': self.product_uom_id and self.product_uom_id.id or False,
            'unit_amount': False,
            'product_id': False,
            'product_uom_id': False,
            #'amount': self.company_currency_id.with_context(date=self.date or fields.Date.context_today(self)).compute(amount, self.analytic_account_id.currency_id) if self.analytic_account_id.currency_id else amount,
            'amount': self.amount_total,
            'general_account_id': account_id,
            'ref': self.name,
            'move_id': self.move_id.id,
            'user_id': self._uid,
            #'tag_ids': tags_id
            #'tag_ids': self.tags_id,
        }
        return vals
    
    @api.multi
    def validate(self):
        #check_total = self.env['res.users'].has_group(
         #   'donation.group_donation_check_total')
        precision = self.env['decimal.precision'].precision_get('Account')
        for income in self:
            if not income.line_ids:
                raise UserError(_(
                    "Cannot validate the income of %s because it doesn't "
                    "have any lines!") % income.responsible_by.partner_id.name)

            if float_is_zero(
                    income.amount_total, precision_digits=precision):
                raise UserError(_(
                    "Cannot validate the Income of %s because the "
                    "total amount is 0 !") % income.responsible_by.partner_id.name)

            if income.state != 1:
                raise UserError(_(
                    "Cannot validate the Income of %s because it is not "
                    "in draft state.") % income.responsible_by.partner_id.name)

            #if check_total and donation.check_total != donation.amount_total:
             #   raise UserError(_(
              #      "The amount of the donation of %s (%s) is different "
               #     "from the sum of the donation lines (%s).") % (
                #    donation.donation_by.partner_id.name, donation.check_total,
                 #   donation.amount_total))
            vals = {'state': 2}
            if income.amount_total:
                move_vals = income._prepare_donation_move()
                move_analytic_vals = income._prepare_analytic_line()[0]
                # when we have a full in-kind donation: no account move
                if move_vals:
                    move = self.env['account.move'].create(move_vals)
                    #move.post()
                    move_id2 = move.id
                    vals['move_id'] = move.id
                    for donation_line in income.line_ids:
                        analytic_account_id = donation_line.get_analytic_account_id()
                        if analytic_account_id:
                            move_analytic = self.env['account.analytic.line'].create(move_analytic_vals)
                            move_analytic2 = move_analytic.id            
                            analytic = donation_line.analytic_account_id.id
                            #account = donation_line.account_id.id
                            #account = donation_line.account_id.id
                            if donation_line.is_visible_prep == True:
                                account = donation_line.account_id.id
                            elif donation_line.is_visible_bank == True:
                                account = donation_line.bank_id.property_account_income_id.id
                            elif donation_line.is_visible_interest == True:
                                account = donation_line.bank_id.property_account_income_id.id
                            elif donation_line.is_visible_discounts == True:
                                account = donation_line.vendor_account.id
                            elif donation_line.is_visible_others == True:
                                account = donation_line.account_id.id
                            amount = donation_line.amount
                        #vals['move_analytic_id'] = move_analytic.id
                            #self.env.cr.execute("insert INTO account_analytic_line_other_income_rel(other_income_id, account_analytic_line_id) VALUES ('%s','%s')" %(donation_line.income_id.id,move_analytic.id))
                        
                            self.env.cr.execute("SELECT id FROM account_move_line where move_id = '%s' and account_id ='%d' and analytic_account_id ='%d' " %(move.id,account,analytic))
                    ##and analytic_account_id ='%d' , analytic
                            res111 = self.env.cr.fetchone()[0]
                            self.env.cr.execute("UPDATE account_analytic_line set move_id= '%s' where id= '%d'" %(res111,move_analytic.id))
                    ##ress = (move.id*2) - 1
                            self.env.cr.execute("UPDATE account_analytic_line set account_id= '%s' where id= '%d'" %(analytic,move_analytic.id))
                        
                            self.env.cr.execute("SELECT credit FROM account_move_line where move_id = '%s' and account_id ='%d' and id ='%d' " %(move.id,account,res111))
                            res111_amount = self.env.cr.fetchone()[0]
                            self.env.cr.execute("UPDATE account_analytic_line set amount= '%s' where id= '%d'" %(amount,move_analytic.id))
                        
                            #resss = donation_line.account_id.id
                            if donation_line.is_visible_prep == True:
                                resss = donation_line.account_id.id
                            elif donation_line.is_visible_bank == True:
                                resss = donation_line.bank_id.property_account_income_id.id
                            elif donation_line.is_visible_interest == True:
                                resss = donation_line.bank_id.property_account_income_id.id
                            elif donation_line.is_visible_discounts == True:
                                resss = donation_line.vendor_account.id
                            elif donation_line.is_visible_others == True:
                                resss = donation_line.account_id.id
                            self.env.cr.execute("UPDATE account_analytic_line set general_account_id= '%s' where id= '%d'" %(resss,move_analytic.id))
                            ##ressss = donation.commercial_partner_id.id
                            ##self.env.cr.execute("UPDATE account_analytic_line set partner_id= '%s' where id= '%d'" %(ressss,move_analytic.id))
                        ##ress2 = move_analytic.id
                else:
                    income.message_post(_(
                        'Full in-kind income: no account move generated'))
            #if (
             ##      donation.tax_receipt_total and
               #     not donation.tax_receipt_id):
                #receipt_vals = donation._prepare_each_tax_receipt()
                #receipt = self.env['donation.tax.receipt'].create(receipt_vals)
                #vals['tax_receipt_id'] = receipt.id
            income.write(vals)
            
            for donation in self:
                for donation_line in donation.line_ids:
                    self.env.cr.execute("select sum(amount) FROM income_line inner join other_income on income_line.income_id = other_income.id where state = 2 and fundstream_id = '%s'" %(donation_line.fundstream_id.id))
                    fund1 = self.env.cr.fetchone()[0]    
                    self.env.cr.execute("update donation_fundstream set total_other = '%s' where id ='%s'" %(fund1,donation_line.fundstream_id.id))
                    
                    self.env.cr.execute("select total_other from donation_fundstream  where id ='%s'" %(donation_line.fundstream_id.id))
                    fund2 = self.env.cr.fetchone()[0]
                    self.env.cr.execute("select cost_budget from donation_fundstream  where id ='%s'" %(donation_line.fundstream_id.id))
                    fund3 = self.env.cr.fetchone()[0]
                    fund4 = fund3 - (fund1+fund2)
                    self.env.cr.execute("update donation_fundstream set difference = '%s' where id ='%s'" %(fund4,donation_line.fundstream_id.id))
                    #if fund3 > 0:
                     #   if fund4 > 0:
                      #      self.env.cr.execute("update donation_fundstream set fund_active = 'True' where id ='%s'" %(donation_line.fundstream_id.id))
                       # else:
                        #    self.env.cr.execute("update donation_fundstream set fund_active = 'False' where id ='%s'" %(donation_line.fundstream_id.id))
                    #else:
                     #   self.env.cr.execute("update donation_fundstream set fund_active = 'False' where id ='%s'" %(donation_line.fundstream_id.id))
        return
    
    
class IncomeLine(models.Model):
    _name = 'income.line'
    _description = 'Income Lines'
    _rec_name = 'requisition_id'
    
    
    @api.multi
    @api.depends(
        'unit_price', 'quantity', 'income_id.currency_id','interest_amount',
        'income_id.income_date', 'income_id.company_id','bank_balance','difference_rate')
    def _compute_amount_company_currency(self):
        for line in self:
            if line.bank_id and line.income_id.income_type.state <> 4:
                amount = line.bank_balance * line.difference_rate
                line.amount = amount
            elif line.bank_id and line.income_id.income_type.state == 4:
                line.amount = line.interest_amount
            else:
                amount = line.quantity * line.unit_price
                line.amount = amount
            #amount = line.amount
            #income_currency = line.income_id.currency_id.with_context(
             #   date=line.income_id.income_date)
            #line.amount_company_currency = income_currency.compute(
             #   amount, line.income_id.company_id.currency_id)
    @api.one
    @api.depends('currency_rate','current_rate')         
    def _compute_difference(self):
        for line in self:
            difference = self.bank_balance 
            line.difference_rate = line.current_rate - line.currency_rate
            
    @api.one
    @api.depends('income_type_id')         
    def _compute_visible(self):
        for line in self:
            if line.income_id.income_type.state in (1,2,3):
                line.is_visible_prep = True
            elif line.income_id.income_type.state == 4:
                line.is_visible_interest = True
            elif line.income_id.income_type.state == 5:
                line.is_visible_bank = True
            elif line.income_id.income_type.state == 6:
                line.is_visible_discounts = True
            elif line.income_id.income_type.state == 7:
                line.is_visible_others = True
                
    is_visible_prep = fields.Boolean(string='Insurance Visible',compute='_compute_visible')
    is_visible_interest = fields.Boolean(string='Interest Visible',compute='_compute_visible')
    is_visible_others = fields.Boolean(string='Others Visible',compute='_compute_visible')
    is_visible_bank = fields.Boolean(string="Bank Visible",compute='_compute_visible')
    is_visible_discounts = fields.Boolean(string="Discounts Visible",compute='_compute_visible')
    income_id = fields.Many2one('other.income', string='Income')
    recipt_number = fields.Char(string='Receipt Number', size=32)
    requisition_id = fields.Many2one('purchase.requisition', string ='Tender')
    partner_id = fields.Many2one('res.partner', string='Vendor', index=True,
        track_visibility='onchange', ondelete='restrict')
    state = fields.Selection([
         (1, 'Draft'),
         (2, 'Transfer'),
         (3, 'Validate'),
         (4, 'Posted'),
         (5, 'Bank')], string='State', related='income_id.state' ,readonly=True, copy=False,
                              default=1,index=True, track_visibility='onchange')
    income_type_id = fields.Many2one('income.type', related='income_id.income_type', 
                                     store=True, string='Type')
    #income_type_state = fields.Selection(related='income_id.income_type.state',
     #                                store=True, string='Type State',ondelete='restrict')
    company_id = fields.Many2one('res.company', string='Company',related='income_id.company_id')
    income_date = fields.Date(related='income_id.income_date', readonly=True, store=True,
                              string='Date')
    responsible_by = fields.Many2one('res.users', string = 'Responsible by',
                                     related='income_id.responsible_by', readonly=True, store=True)
    quantity = fields.Integer(string='Quantity', default=1)
    unit_price = fields.Monetary(string='Unit Price', digits=dp.get_precision('Account'),
        currency_field='currency_id')
    amount = fields.Monetary(string='Amount',store=True,compute='_compute_amount_company_currency',
                             currency_field='currency_id', digits=dp.get_precision('Account'))
    amount_company_currency = fields.Monetary(compute='_compute_amount_company_currency',
        string='Amount in Company Currency',currency_field='company_currency_id',
        digits=dp.get_precision('Account'), store=True)
    
    account_id = fields.Many2one('account.account',related='payment_method.account_id', 
                                 string='Account', store=True)
    sequence = fields.Integer('Sequence')
    payment_method = fields.Many2one('income.method',store=True,string = 'Payment Method')
    currency_id = fields.Many2one(
        'res.currency', related='income_id.currency_id', readonly=True)
    company_currency_id = fields.Many2one(
        'res.currency', related='income_id.company_id.currency_id',readonly=True)
    
    bank_id = fields.Many2one('res.bank',string='Bank',store=True)
    bank_account=fields.Many2one('account.account',related='bank_id.property_account_income_id',string='Bank Account')
    bank_balance = fields.Float(related='bank_id.balance',string='Bank Balance',store=True)
    currency_rate = fields.Float(related='bank_id.currency_rate',string='Currency Rate',store=True)
    current_rate = fields.Float(string='Current Rate', store=True)
    difference_rate = fields.Float(string="Difference Rate", compute="_compute_difference", store=True)
    interest_amount = fields.Float(string='Interest Amount', store=True)
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    invoice_vendor = fields.Many2one('res.partner', related='invoice_id.partner_id')
    invoice_source = fields.Char(related='invoice_id.origin', string='Invoice Source')
    vendor_account = fields.Many2one('account.account',related='invoice_vendor.property_account_receivable_id')
    fundstream_id = fields.Many2one('donation.fundstream', string='FundStream',track_visibility='onchange', ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account',related='fundstream_id.analytic_account_id', string='Analytic Account', readonly=True, store=True)
     
    @api.model
    def get_analytic_account_id(self):
        #self.analytic2 = self.analytic_account_id.id
        return self.analytic_account_id.id or False 
        #return self.analytic_account_id.id or False
    
    
    @api.model
    def get_account_id(self):
        if self.is_visible_prep == True:
            return self.account_id.id or False 
        elif self.is_visible_bank == True:
            return self.bank_id.property_account_income_id.id or False
        elif self.is_visible_interest == True:
            return self.bank_id.property_account_income_id.id or False
        elif self.is_visible_discounts == True:
            return self.vendor_account.id or False
        elif self.is_visible_others == True:
            return self.account_id.id or False