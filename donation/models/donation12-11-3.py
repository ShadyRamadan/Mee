# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
from openerp.tools import float_is_zero, float_compare
import openerp.addons.decimal_precision as dp


class DonationDonation(models.Model):
    _name = 'donation.donation'
    _description = 'Donation'
    _order = 'id desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    @api.multi
    @api.depends(
        'line_ids', 'line_ids.unit_price', 'line_ids.quantity',
        'line_ids.product_id', 'donation_date', 'currency_id', 'company_id')
    def _compute_total(self):
        for donation in self:
            total = tax_receipt_total = 0.0
            company_currency = donation.company_currency_id
            donation_currency = donation.currency_id
            # Do not consider other currencies for tax receipts
            # because, for the moment, only very very few countries
            # accept tax receipts from other countries, and never in another
            # currency. If you know such cases, please tell us and we will
            # update the code of this module
            for line in donation.line_ids:
                line_total = line.quantity * line.unit_price
                total += line_total
                if (
                        donation_currency == company_currency and
                        line.product_id.tax_receipt_ok):
                    tax_receipt_total += line_total

            donation.amount_total = total
            donation_currency =\
                donation.currency_id.with_context(date=donation.donation_date)
            total_company_currency = donation_currency.compute(
                total, donation.company_id.currency_id)
            donation.amount_total_company_currency = total_company_currency
            donation.tax_receipt_total = tax_receipt_total

    # We don't want a depends on partner_id.country_id, because if the partner
    # moves to another country, we want to keep the old country for
    # past donations to have good statistics
    @api.multi
    @api.depends('donation_by')
    def _compute_country_id(self):
        # Use sudo() to by-pass record rules, because the same partner
        # can have donations in several companies
        for donation in self:
            donation.sudo().country_id = donation.donation_by.partner_id.country_id

    @api.model
    def _default_currency(self):
        company = self.env['res.company']._company_default_get(
            'donation.donation')
        return company.currency_id
    
    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        states={3: [('readonly', True)]},
        track_visibility='onchange', ondelete='restrict',
        default=_default_currency)
    partner_id = fields.Many2one(
        'res.partner', string='Donor', index=True,
        states={3: [('readonly', True)]},
        track_visibility='onchange', ondelete='restrict')
    commercial_partner_id = fields.Many2one(
        related='donation_by.partner_id.commercial_partner_id',
        string='Parent Donor', readonly=True, store=True, index=True)
    # country_id is here to have stats per country
    # WARNING : I can't put a related field, because when someone
    # writes on the country_id of a partner, it will trigger a write
    # on all it's donations, including donations in other companies
    # which will be blocked by the record rule
    country_id = fields.Many2one(
        'res.country', string='Country', compute='_compute_country_id',
        store=True, readonly=True, copy=False)
    donation_by = fields.Many2one('res.users',
                                   'Donation by',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    
    donation_place = fields.Many2one('donation.place','Donation Place', store=True)
    donation_section = fields.Many2one('donation.section','Section', store=True, required=True)
    gov_id = fields.Many2one('govs.villages.gov',related = 'donation_by.gov_id' ,string='Gov', store=True)
    check_total = fields.Monetary(
        string='Check Amount', digits=dp.get_precision('Account'),
        states={3: [('readonly', True)]}, currency_field='currency_id',
        track_visibility='onchange')
    amount_total = fields.Monetary(
        compute='_compute_total', string='Amount Total',
        currency_field='currency_id', store=True,
        digits=dp.get_precision('Account'), readonly=True)
    amount_total_company_currency = fields.Monetary(
        compute='_compute_total', string='Amount Total in Company Currency',
        currency_field='company_currency_id',
        store=True, digits=dp.get_precision('Account'), readonly=True)
    donation_date = fields.Date(
        string='Donation Date', required=True,default=fields.Date.context_today,
        states={3: [('readonly', True)]}, index=True,
        track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        states={3: [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get(
            'donation.donation'))
    line_ids = fields.One2many(
        'donation.line', 'donation_id', string='Donation Lines',
        states={3: [('readonly', True)]}, copy=True)
    move_id = fields.Many2one(
        'account.move', string='Account Move', readonly=True, copy=False)
    move_analytic_id = fields.Many2many(
        'account.analytic.line', string='Account Analytic', readonly=True)
    
    number = fields.Char(
        related='move_id.name', readonly=True, size=64,
        store=True, string='Donation Number')
    journal_id = fields.Many2one(
        'account.journal', string='Payment Method', required=True,related = "donation_section.journal_id",
        domain=[
            ('type', 'in', ('bank', 'cash')),
            ('allow_donation', '=', True)],
        states={3: [('readonly', True)]},
        track_visibility='onchange',
        default=lambda self: self.env.user.context_donation_journal_id)
    payment_ref = fields.Char(
        string='Payment Reference', size=32,
        states={3: [('readonly', True)]})
    state = fields.Selection([
        (1, 'Draft'),
        (2, 'Transfer'),
        (3, 'Done'),
        (4, 'Cancelled'),
        ], string='State', readonly=True, copy=False, default=1,
        index=True, track_visibility='onchange')
    company_currency_id = fields.Many2one(
        related='company_id.currency_id', string="Company Currency",
        readonly=True)
    campaign_id = fields.Many2one(
        'donation.campaign', string='Donation Campaign',
        track_visibility='onchange', ondelete='restrict',
        default=lambda self: self.env.user.context_donation_campaign_id)
    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name',
        readonly=True)
    #display_tag = fields.Char(string ='Tag')
    tax_receipt_id = fields.Many2one(
        'donation.tax.receipt', string='Tax Receipt', readonly=True,
        copy=False)
    tax_receipt_option = fields.Selection([
        ('none', 'None'),
        ('each', 'For Each Donation'),
        ('annual', 'Annual Tax Receipt'),
        ], string='Tax Receipt Option', states={3: [('readonly', True)]},
        index=True)
    tax_receipt_total = fields.Monetary(
        compute='_compute_total', string='Eligible Tax Receipt Sub-total',
        store=True, currency_field='company_currency_id')
    tags_id = fields.Many2many('account.analytic.tag',string = 'Tags', readonly=True)
    donation_method = fields.Many2one('donation.instrument' ,store=True,string = 'Donation Method')
    account_id = fields.Many2one('account.account' ,related='donation_place.account_id',store=True,string = 'Account',readonly=True )
    product_id = fields.Many2one(
        'product.product', domain=[('donation', '=', True)], string='Product', required=True,
         ondelete='restrict')
    #analytic = fields.Integer(string="id",compute='get_analytic_account_id_2')
    #analytic_tag = fields.Integer(string="tegid",compute='get_analytic_account_id_2')

    @api.multi
    @api.constrains('donation_date')
    def _check_donation_date(self):
        for donation in self:
            if donation.donation_date > fields.Date.context_today(self):
                # TODO No error pop-up to user : Odoo 9 BUG ?
                raise ValidationError(_(
                    'The date of the donation of %s should be today '
                    'or in the past, not in the future!')
                    % donation.donation_by.partner_id.name)

    @api.multi
    def _prepare_each_tax_receipt(self):
        self.ensure_one()
        vals = {
            'company_id': self.company_id.id,
            'currency_id': self.company_currency_id.id,
            'donation_date': self.donation_date,
            'amount': self.tax_receipt_total,
            'type': 'each',
            'partner_id': self.commercial_partner_id.id,
        }
        return vals

    @api.model
    def _prepare_move_line_name(self):
        name = _('Donation of %s') % self.donation_by.partner_id.name
        return name

    @api.multi
    def _prepare_counterpart_move_line(
            self, name, amount_total_company_cur, total_amount_currency,
            currency_id):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Account')
        if float_compare(
                amount_total_company_cur, 0, precision_digits=precision) == 1:
            debit = amount_total_company_cur
            credit = 0
            total_amount_currency = self.amount_total
        else:
            credit = amount_total_company_cur * -1
            debit = 0
            total_amount_currency = self.amount_total * -1
        vals = {
            'debit': debit,
            'credit': credit,
            'name': name,
            'account_id': self.journal_id.default_debit_account_id.id,
            'partner_id': self.commercial_partner_id.id,
            'currency_id': currency_id,
            'amount_currency': (
                currency_id and total_amount_currency or 0.0),
            }
        return vals

    @api.multi
    def _prepare_donation_move(self):
        self.ensure_one()
        if not self.journal_id.default_debit_account_id:
            raise UserError(
                _("Missing Default Debit Account on journal '%s'.")
                % self.journal_id.name)

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
        for donation_line in self.line_ids:
            if donation_line.in_kind:
                continue
            amount_total_company_cur += donation_line.amount_company_currency
            #account_id = donation_line.product_id.property_account_income_id.id
            #if not account_id:
             #   account_id = donation_line.product_id.categ_id.\
              #      property_account_income_categ_id.id
            account_id = donation_line.get_account_id()
            if not account_id:
                raise UserError(
                    _("Missing income account on product '%s' or on it's "
                        "related product category")
                    % donation_line.product_id.name)
            analytic_account_id = donation_line.get_analytic_account_id()
            
            amount_currency = 0.0
            if float_compare(
                    donation_line.amount_company_currency, 0,
                    precision_digits=precision) == 1:
                credit = donation_line.amount_company_currency
                debit = 0
                amount_currency = donation_line.amount * -1
            else:
                debit = donation_line.amount_company_currency * -1
                credit = 0
                amount_currency = donation_line.amount

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
                'partner_id': self.commercial_partner_id.id,
                'currency_id': currency_id,
                'amount_currency': (
                    currency_id and content['amount_currency'] or 0.0),
                }))

        # counter-part
        ml_vals = self._prepare_counterpart_move_line(
            name, amount_total_company_cur, total_amount_currency,
            currency_id)
        movelines.append((0, 0, ml_vals))

        vals = {
            'journal_id': self.journal_id.id,
            'date': self.donation_date,
            'ref': self.payment_ref,
            'line_ids': movelines,
            }
        return vals
    
    @api.one
    def _prepare_analytic_line(self):
        """ Prepare the values used to create() an account.analytic.line upon validation of an account.move.line having
            an analytic account. This method is intended to be extended in other modules.
        """
        #for donation_line in self.line_ids:
            #if donation_line.in_kind:
                #continue
        #amount = (self.credit or 0.0) - (self.debit or 0.0)
        #account_id = self.line_ids.product_id.property_account_income_id.id
        for donation_line in self.line_ids:
            if donation_line.in_kind:
                continue
            account_id = donation_line.get_account_id()
            analytic_account_id = donation_line.get_analytic_account_id()
        #if not account_id:
         #   account_id = self.line_ids.product_id.categ_id.property_account_income_categ_id.id    
        name = self._prepare_move_line_name()
        vals = {
            'name': name,
            'date': self.donation_date,
            'account_id': analytic_account_id,
            'partner_id': self.commercial_partner_id.id,
            #'unit_amount': self.quantity,
            #'product_id': self.product_id and self.product_id.id or False,
            #'product_uom_id': self.product_uom_id and self.product_uom_id.id or False,
            'unit_amount': False,
            'product_id': False,
            'product_uom_id': False,
            #'amount': self.company_currency_id.with_context(date=self.date or fields.Date.context_today(self)).compute(amount, self.analytic_account_id.currency_id) if self.analytic_account_id.currency_id else amount,
            'amount': self.amount_total,
            'general_account_id': account_id,
            'ref': self.payment_ref,
            'move_id': self.move_id.id,
            'user_id': self._uid,
            'tag_ids': self.tags_id,
        }
        return vals
    
    @api.multi   
    def transfer(self):
        for rec in self:
            rec.state = 2
            #self.env.cr.execute("SELECT place.tag_id FROM donation_donation inner join donation_place as place on donation_donation.donation_place = place.id where donation_donation.id= '%s'" %(self.id))
            #res = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id) VALUES ('%s','%s')" %(rec.line_ids.id,res))
            
            #self.env.cr.execute("SELECT gov.tag_id FROM donation_donation inner join govs_villages_gov as gov on donation_donation.gov_id = gov.id where donation_donation.id= '%s'" %(self.id))
            #res2 = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id) VALUES ('%s','%s')" %(rec.line_ids.id,res2))

            #self.env.cr.execute("SELECT method.tag_id FROM donation_line inner join donation_instrument as method on donation_line.donation_method = method.id where donation_line.id= '%s'" %(self.line_ids.id))
            #res3 = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id) VALUES ('%s','%s')" %(rec.line_ids.id,res3))
            
            self.env.cr.execute("SELECT place.tag_id FROM donation_donation inner join donation_place as place on donation_donation.donation_place = place.id where donation_donation.id= '%s'" %(self.id))
            res11 = self.env.cr.fetchone()[0]
            rec.env.cr.execute("insert INTO account_analytic_tag_donation_donation_rel(donation_donation_id, account_analytic_tag_id) VALUES ('%s','%s')" %(rec.id,res11))
            
            self.env.cr.execute("SELECT gov.tag_id FROM donation_donation inner join govs_villages_gov as gov on donation_donation.gov_id = gov.id where donation_donation.id= '%s'" %(self.id))
            res12 = self.env.cr.fetchone()[0]
            rec.env.cr.execute("insert INTO account_analytic_tag_donation_donation_rel(donation_donation_id, account_analytic_tag_id) VALUES ('%s','%s')" %(rec.id,res12))

            self.env.cr.execute("SELECT method.tag_id FROM donation_donation inner join donation_instrument as method on donation_donation.donation_method = method.id where donation_donation.id= '%s'" %(self.id))
            res13 = self.env.cr.fetchone()[0]
            rec.env.cr.execute("insert INTO account_analytic_tag_donation_donation_rel(donation_donation_id, account_analytic_tag_id) VALUES ('%s','%s')" %(rec.id,res13))
        for donation_line in self.line_ids:
            self.env.cr.execute("SELECT place.tag_id FROM donation_line inner join donation_place as place on donation_line.donation_place = place.id where donation_line.id= '%s'" %(donation_line.id))
            res11 = self.env.cr.fetchone()[0]
            rec.env.cr.execute("insert INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id) VALUES ('%s','%s')" %(donation_line.id,res11))
            
            self.env.cr.execute("SELECT gov.tag_id FROM donation_line inner join govs_villages_gov as gov on donation_line.gov_id = gov.id where donation_line.id= '%s'" %(donation_line.id))
            res12 = self.env.cr.fetchone()[0]
            rec.env.cr.execute("insert INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id) VALUES ('%s','%s')" %(donation_line.id,res12))
            
            self.env.cr.execute("SELECT method.tag_id FROM donation_line inner join donation_instrument as method on donation_line.donation_method = method.id where donation_line.id= '%s'" %(donation_line.id))
            res13 = self.env.cr.fetchone()[0]
            rec.env.cr.execute("insert INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id) VALUES ('%s','%s')" %(donation_line.id,res13))
                        
    @api.multi
    def validate(self):
        check_total = self.env['res.users'].has_group(
            'donation.group_donation_check_total')
        precision = self.env['decimal.precision'].precision_get('Account')
        for donation in self:
            if not donation.line_ids:
                raise UserError(_(
                    "Cannot validate the donation of %s because it doesn't "
                    "have any lines!") % donation.donation_by.partner_id.name)

            if float_is_zero(
                    donation.amount_total, precision_digits=precision):
                raise UserError(_(
                    "Cannot validate the donation of %s because the "
                    "total amount is 0 !") % donation.donation_by.partner_id.name)

            if donation.state != 2:
                raise UserError(_(
                    "Cannot validate the donation of %s because it is not "
                    "in transfer state.") % donation.donation_by.partner_id.name)

            if check_total and donation.check_total != donation.amount_total:
                raise UserError(_(
                    "The amount of the donation of %s (%s) is different "
                    "from the sum of the donation lines (%s).") % (
                    donation.donation_by.partner_id.name, donation.check_total,
                    donation.amount_total))
            vals = {'state': 3}
            if donation.amount_total:
                move_vals = donation._prepare_donation_move()
                move_analytic_vals = donation._prepare_analytic_line()[0]
                # when we have a full in-kind donation: no account move
                if move_vals:
                    move = self.env['account.move'].create(move_vals)
                    #move.post()
                    move_id2 = move.id
                    vals['move_id'] = move.id
                    
                    for donation_line in self.line_ids:
                        move_analytic = self.env['account.analytic.line'].create(move_analytic_vals)
                        move_analytic2 = move_analytic.id            
                        analytic = donation_line.analytic_account2.id
                        account = donation_line.account_id.id
                        #vals['move_analytic_id'] = move_analytic.id
                        self.env.cr.execute("insert INTO account_analytic_line_donation_donation_rel(donation_donation_id, account_analytic_line_id) VALUES ('%s','%s')" %(donation_line.donation_id.id,move_analytic.id))
                        
                        self.env.cr.execute("SELECT id FROM account_move_line where move_id = '%s' and account_id ='%d' and analytic_account_id ='%d' " %(move.id,account,analytic))
                    #and analytic_account_id ='%d' , analytic
                        res111 = self.env.cr.fetchone()[0]
                        self.env.cr.execute("UPDATE account_analytic_line set move_id= '%s' where id= '%d'" %(res111,move_analytic.id))
                    #ress = (move.id*2) - 1
                        self.env.cr.execute("UPDATE account_analytic_line set account_id= '%s' where id= '%d'" %(analytic,move_analytic.id))
                        
                        self.env.cr.execute("SELECT credit FROM account_move_line where move_id = '%s' and account_id ='%d' and id ='%d' " %(move.id,account,res111))
                        res111_amount = self.env.cr.fetchone()[0]
                        self.env.cr.execute("UPDATE account_analytic_line set amount= '%s' where id= '%d'" %(res111_amount,move_analytic.id))
                        
                        
                        resss = self.account_id.id
                        self.env.cr.execute("UPDATE account_analytic_line set general_account_id= '%s' where id= '%d'" %(resss,move_analytic.id))
                        ressss = self.commercial_partner_id.id
                        self.env.cr.execute("UPDATE account_analytic_line set partner_id= '%s' where id= '%d'" %(ressss,move_analytic.id))
                        ress2 = move_analytic.id
                        self.env.cr.execute("SELECT place.tag_id FROM donation_donation inner join donation_place as place on donation_donation.donation_place = place.id where donation_donation.id= '%s'" %(self.id))
                        res11 = self.env.cr.fetchone()[0]
                        self.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress2,res11))
                        self.env.cr.execute("SELECT gov.tag_id FROM donation_donation inner join govs_villages_gov as gov on donation_donation.gov_id = gov.id where donation_donation.id= '%s'" %(self.id))
                        res12 = self.env.cr.fetchone()[0]
                        self.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress2,res12))
                        self.env.cr.execute("SELECT method.tag_id FROM donation_donation inner join donation_instrument as method on donation_donation.donation_method = method.id where donation_donation.id= '%s'" %(self.id))
                        res13 = self.env.cr.fetchone()[0]
                        self.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress2,res13))
                else:
                    donation.message_post(_(
                        'Full in-kind donation: no account move generated'))
            if (
                    donation.tax_receipt_option == 'each' and
                    donation.tax_receipt_total and
                    not donation.tax_receipt_id):
                receipt_vals = donation._prepare_each_tax_receipt()
                receipt = self.env['donation.tax.receipt'].create(receipt_vals)
                vals['tax_receipt_id'] = receipt.id
            donation.write(vals)
        return

    @api.multi
    def save_default_values(self):
        self.ensure_one()
        self.env.user.write({
            'context_donation_journal_id': self.journal_id.id,
            'context_donation_campaign_id': self.campaign_id.id,
            })
        
    #@api.multi
    #def analytic(self):
    #    for rec in self:
     #       ress = (self.move_id.id *2) - 1
      #      self.env.cr.execute("UPDATE account_analytic_line set move_id= '%s' where id= '%d'" %(ress,self.move_analytic_id.id))
            
       #     ress2 = self.move_analytic_id.id
        #    self.env.cr.execute("SELECT place.tag_id FROM donation_donation inner join donation_place as place on donation_donation.donation_place = place.id where donation_donation.id= '%s'" %(self.id))
         #   res11 = self.env.cr.fetchone()[0]
          #  rec.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress2,res11))
            
           # self.env.cr.execute("SELECT gov.tag_id FROM donation_donation inner join govs_villages_gov as gov on donation_donation.gov_id = gov.id where donation_donation.id= '%s'" %(self.id))
            #res12 = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress2,res12))

            #self.env.cr.execute("SELECT method.tag_id FROM donation_donation inner join donation_instrument as method on donation_donation.donation_method = method.id where donation_donation.id= '%s'" %(self.id))
            #res13 = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress2,res13))
            
            #self.env.cr.execute("SELECT place.tag_id FROM donation_donation inner join donation_place as place on donation_donation.donation_place = place.id where donation_donation.id= '%s'" %(self.id))
            #res11 = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress,res11))
            
            #self.env.cr.execute("SELECT gov.tag_id FROM donation_donation inner join govs_villages_gov as gov on donation_donation.gov_id = gov.id where donation_donation.id= '%s'" %(self.id))
            #res12 = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress,res12))

            #self.env.cr.execute("SELECT method.tag_id FROM donation_donation inner join donation_instrument as method on donation_donation.donation_method = method.id where donation_donation.id= '%s'" %(self.id))
            #res13 = self.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_line_tag_rel(line_id, tag_id) VALUES ('%s','%s')" %(ress,res13)) 
    @api.multi
    def done2cancel(self):
        '''from Done state to Cancel state'''
        for donation in self:
            if donation.tax_receipt_id:
                raise UserError(_(
                    "You cannot cancel this donation because "
                    "it is linked to the tax receipt %s. You should first "
                    "delete this tax receipt (but it may not be legally "
                    "allowed).")
                    % donation.tax_receipt_id.number)
            if donation.move_id:
                donation.move_id.button_cancel()
                donation.move_id.unlink()
            donation.state = 4

    @api.multi
    def cancel2draft(self):
        '''from Cancel state to Draft state'''
        for donation in self:
            if donation.move_id:
                raise UserError(_(
                    "A cancelled donation should not be linked to "
                    "an account move"))
            if donation.tax_receipt_id:
                raise UserError(_(
                    "A cancelled donation should not be linked to "
                    "a tax receipt"))
            donation.state = 1

    @api.multi
    def unlink(self):
        for donation in self:
            if donation.state == 3:
                raise UserError(_(
                    "The donation '%s' is in Done state, so you cannot "
                    "delete it.") % donation.display_name)
            if donation.move_id:
                raise UserError(_(
                    "The donation '%s' is linked to an account move, "
                    "so you cannot delete it.") % donation.display_name)
            if donation.tax_receipt_id:
                raise UserError(_(
                    "The donation '%s' is linked to the tax receipt %s, "
                    "so you cannot delete it.")
                    % (donation.display_name, donation.tax_receipt_id.number))
        return super(DonationDonation, self).unlink()

    @api.multi
    @api.depends('state', 'donation_by', 'move_id')
    def _compute_display_name(self):
        for donation in self:
            if donation.state == 1:
                name = _('Draft Donation of %s') % donation.donation_by.partner_id.name
            elif donation.state == 4:
                name = _('Cancelled Donation of %s') % donation.donation_by.partner_id.name
            else:
                name = donation.number
            donation.display_name = name

    @api.onchange('donation_by')
    def partner_id_change(self):
        if self.donation_by.partner_id:
            self.tax_receipt_option = self.donation_by.partner_id.tax_receipt_option

    @api.onchange('tax_receipt_option')
    def tax_receipt_option_change(self):
        res = {}
        if (
                self.donation_by.partner_id and
                self.donation_by.partner_id.tax_receipt_option == 'annual' and
                self.tax_receipt_option != 'annual'):
            res = {
                'warning': {
                    'title': _('Error:'),
                    'message':
                    _('You cannot change the Tax Receipt '
                        'Option when it is Annual.'),
                    },
                }
            self.tax_receipt_option = 'annual'
        return res


class DonationLine(models.Model):
    _name = 'donation.line'
    _description = 'Donation Lines'
    _rec_name = 'product_id'
    
    @api.onchange('donation_id.donation_method')
    def onchange_donation_method(self):
        res = {}
        res['domain'] = {'product_id': [('donation_method', '=', donation_id.donation_method.id)]}
        return res

    @api.multi
    @api.depends(
        'unit_price', 'quantity', 'donation_id.currency_id',
        'donation_id.donation_date', 'donation_id.company_id')
    def _compute_amount_company_currency(self):
        for line in self:
            amount = line.quantity * line.unit_price
            line.amount = amount
            donation_currency = line.donation_id.currency_id.with_context(
                date=line.donation_id.donation_date)
            line.amount_company_currency = donation_currency.compute(
                amount, line.donation_id.company_id.currency_id)

    donation_id = fields.Many2one(
        'donation.donation', string='Donation', ondelete='cascade')
    recipt_number = fields.Char(
        string='Recipt Number', size=32)
    state = fields.Selection([
        (1, 'Draft'),
        (2, 'Transfer'),
        (3, 'Done'),
        (4, 'Cancelled'),
        ], string='State', related='donation_id.state' ,readonly=True, copy=False, default=1,
        index=True, track_visibility='onchange')
    currency_id = fields.Many2one(
        'res.currency', related='donation_id.currency_id', readonly=True)
    company_currency_id = fields.Many2one(
        'res.currency', related='donation_id.company_id.currency_id',
        readonly=True)
    product_id = fields.Many2one(
        'product.product', related='donation_id.product_id', readonly=True, store=True, string='Product',
         ondelete='restrict')
    
    gov_id = fields.Many2one(
        'govs.villages.gov', related='donation_id.gov_id', readonly=True, store=True, string='Gov',
         ondelete='restrict')
    
    donation_date = fields.Date(related='donation_id.donation_date', readonly=True, store=True, string='Date')
    donation_place = fields.Many2one('donation.place',related='donation_id.donation_place', readonly=True, store=True, string='Place')
    partner_id = fields.Many2one(
        'res.partner', string='Donor', required=True, index=True,
        track_visibility='onchange', ondelete='restrict')
    donation_by = fields.Many2one('res.users', string = 'Donation by',related='donation_id.donation_by', readonly=True, store=True)
    donation_collector = fields.Many2one('res.partner', string='Collector', track_visibility='onchange')
    quantity = fields.Integer(string='Quantity', default=1)
    unit_price = fields.Monetary(
        string='Unit Price', digits=dp.get_precision('Account'),
        currency_field='currency_id')
    amount = fields.Monetary(
        compute='_compute_amount_company_currency', string='Amount',
        currency_field='currency_id', digits=dp.get_precision('Account'),
        store=True)
    amount_company_currency = fields.Monetary(
        compute='_compute_amount_company_currency',
        string='Amount in Company Currency',
        currency_field='company_currency_id',
        digits=dp.get_precision('Account'), store=True)
    campaign_id = fields.Many2one(
        'donation.campaign', string='Donation Campaign',
        track_visibility='onchange', ondelete='restrict',
        default=lambda self: self.env.user.context_donation_campaign_id)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        domain=[('account_type', '!=', 'closed')], ondelete='restrict')
    #campaign_id = fields.Many2one(
    analytic_account2 = fields.Many2one('account.analytic.account',related='campaign_id.analytic_account_id', string='Analytic Account', readonly=True, store=True)
    account_id = fields.Many2one('account.account',related='donation_id.donation_place.account_id', string='Account', readonly=True, store=True)
    #analytic2 = fields.Integer(string = 'id', compute='get_analytic_account_id_3',store=True)
    #analytic3 = fields.Integer(string = 'id2',related='analytic_account_id.id' ,store=True)
    sequence = fields.Integer('Sequence')
    # for the fields tax_receipt_ok and in_kind, we made an important change
    # between v8 and v9: in v8, it was a reglar field set by an onchange
    # in v9, it is a related stored field
    tax_receipt_ok = fields.Boolean(
        related='product_id.tax_receipt_ok', readonly=True, store=True)
    donation_method = fields.Many2one(related='donation_id.donation_method', readonly=True, store=True,string = 'Method')
    in_kind = fields.Boolean(
        related='product_id.in_kind_donation', readonly=True, store=True,
        string='In Kind')
    tags_id = fields.Many2many('account.analytic.tag',string = 'Tags', readonly=True)
    
    @api.onchange('donation_id.product_id')
    def product_id_change(self):
        if donation_id.product_id:
            # We should change that one day...
            if donation_id.product_id.list_price:
                self.unit_price = donation_id.product_id.list_price
            
            #self.env.cr.execute("INSERT INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id)VALUES ('%s', '%d')" %(self.id,))
    #@api.one
    #@api.depends('analytic_account_id', 'analytic_account2')
    #@api.model
    #def get_analytic_account_id_3(self):
        #for rec in self:
            #rec.env.cr.execute("SELECT method.tag_id FROM donation_line inner join donation_instrument as method on donation_line.donation_method = method.id where donation_line.id= '%s'" %(rec.id))
            #res = rec.env.cr.fetchone()[0]
            #rec.env.cr.execute("insert INTO account_analytic_tag_donation_line_rel(donation_line_id, account_analytic_tag_id) VALUES ('%s','%s')" %(rec.id,res))11
            #rec.analytic_tag = 1
    #@api.one
    #@api.depends('analytic_account2')
    #@api.model
    #def get_analytic_account_id_2(self):
        #self.analytic2 = self.analytic_account_id.id
     #   return self.analytic_account2.id or False 
        #return self.analytic_account_id.id or False
    
    @api.model
    def get_analytic_account_id(self):
        #self.analytic2 = self.analytic_account_id.id
        return self.analytic_account2.id or False 
        #return self.analytic_account_id.id or False
    @api.model
    def get_account_id(self):
        #self.analytic2 = self.analytic_account_id.id
        return self.account_id.id or False 

class DonationTaxReceipt(models.Model):
    _inherit = 'donation.tax.receipt'

    donation_ids = fields.One2many(
        'donation.donation', 'tax_receipt_id', string='Related Donations')

    @api.model
    def update_tax_receipt_annual_dict(
            self, tax_receipt_annual_dict, start_date, end_date, precision):
        super(DonationTaxReceipt, self).update_tax_receipt_annual_dict(
            tax_receipt_annual_dict, start_date, end_date, precision)
        donations = self.env['donation.donation'].search([
            ('donation_date', '>=', start_date),
            ('donation_date', '<=', end_date),
            ('tax_receipt_option', '=', 'annual'),
            ('tax_receipt_id', '=', False),
            ('tax_receipt_total', '!=', 0),
            ('company_id', '=', self.env.user.company_id.id),
            ('state', '=', 3),
            ])
        for donation in donations:
            tax_receipt_amount = donation.tax_receipt_total
            if float_is_zero(tax_receipt_amount, precision_digits=precision):
                continue
            partner = donation.commercial_partner_id
            if partner not in tax_receipt_annual_dict:
                tax_receipt_annual_dict[partner] = {
                    'amount': tax_receipt_amount,
                    'extra_vals': {
                        'donation_ids': [(6, 0, [donation.id])]},
                    }
            else:
                tax_receipt_annual_dict[partner]['amount'] +=\
                    tax_receipt_amount
                tax_receipt_annual_dict[partner]['extra_vals'][
                    'donation_ids'][0][2].append(donation.id)
