# -*- coding: utf-8 -*-

import re

from openerp import api, fields, models, _
from openerp.osv import expression
import datetime
from openerp.exceptions import UserError

class Bank(models.Model):
    _description = 'Bank'
    _name = 'res.bank'
    _inherit = 'res.bank'
    
    @api.depends('opening_balance')
    def _compute_balance(self):
        for bank in self:
            bank.balance = self.opening_balance
            
    property_account_income_id = fields.Many2one('account.account', company_dependent=True,
        string="Income Account", oldname="property_account_income",
        domain=[('deprecated', '=', False)])
    
    property_account_expense_id = fields.Many2one('account.account', company_dependent=True,
        string="Expense Account", oldname="property_account_expense",
        domain=[('deprecated', '=', False)])
    
    opening_balance = fields.Float(string='Opening Balance', store=True)
    
    currency_rate = fields.Float(string='Currency Rate', store=True)
    current_balance = fields.Float(string='Total Transfer',compute='_compute_balance')
    balance =fields.Float(string='Balance',compute='_compute_balance')
    
    @api.multi
    @api.depends('property_account_income_id')
    def _compute_balance(self):
        res = 0.0
        res2 = 0.0
        balance = 0.0
        d = d1 = datetime.datetime.today()
        for rec in self:
            if rec.property_account_income_id:
                self.env.cr.execute("SELECT count(id) FROM account_move_line WHERE account_id = '%s' and state = 'posted' and date < '%s'" %(rec.property_account_income_id.id,d))
                count = self.env.cr.fetchone()[0]
                if count > 0:
                    self.env.cr.execute("SELECT sum(debit) FROM account_move_line WHERE account_id = '%s' and state = 'posted' and date < '%s'" %(rec.property_account_income_id.id,d))
                    res = self.env.cr.fetchone()[0]
                else:
                    res = 0.0
                self.env.cr.execute("SELECT count(id) FROM account_move_line WHERE account_id = '%s' and state = 'posted' and date < '%s'" %(rec.property_account_income_id.id,d))
                count2 = self.env.cr.fetchone()[0]
                if count2 > 0:
                    self.env.cr.execute("SELECT sum(credit) FROM account_move_line WHERE account_id = '%s' and state = 'posted' and date < '%s'" %(rec.property_account_income_id.id,d))
                    res2 = self.env.cr.fetchone()[0]
                else:
                    res2 = 0.0
                balance = res - res2
                rec.current_balance = balance
                rec.balance = rec.opening_balance + rec.current_balance
        return True