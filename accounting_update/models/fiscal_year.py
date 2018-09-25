# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.addons import decimal_precision as dp
import logging
from itertools import chain
from odoo.http import request

_logger = logging.getLogger(__name__)
concat = chain.from_iterable

class AccountFiscalYear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"
    _order = "date_start, id"
    
    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    state = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', copy=False, default='draft')
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    end_journal_period_id = fields.Many2one('account.journal.period', 'End of Year Entries Journal',readonly=True, copy=False)
    
    def _check_duration(self):
        if self.date_stop < self.date_start:
            return False
        return True
    
    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_start','date_stop'])
    ]
    
    def create_period3(self):
        period_object = self.env['account.period'].browse(fy.date_start)
        period_ids = period_object.search([])
        interval=3
        #period_obj = self.pool.get('account.period')
        #for fy in self.browse(cr, uid, ids, context=context):
        for fy in self:
            #period_date = period_object.browse(fy.date_start)
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            vals = {
                'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_start': ds,
                'date_stop': ds,
                'special': True,
                'fiscalyear_id': fy.id,
                }
            opening_period = self.env['account.period'].create(vals)
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)
                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')
                vals2 = {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                }
                period = self.env['account.period'].create(vals2)
                ds = ds + relativedelta(months=interval)
        return

    def create_period(self):
        period_object = self.env['account.period']
        period_ids = period_object.search([])
        interval=1
        #period_obj = self.pool.get('account.period')
        #for fy in self.browse(cr, uid, ids, context=context):
        for fy in self:
            #period_date = period_object.browse(fy.date_start)
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            vals = {
                'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_start': ds,
                'date_stop': ds,
                'special': True,
                'fiscalyear_id': fy.id,
                }
            opening_period = self.env['account.period'].create(vals)
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)
                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')
                vals2 = {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                }
                period = self.env['account.period'].create(vals2)
                ds = ds + relativedelta(months=interval)
        return