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

class account_journal_period(models.Model):
    _name = "account.journal.period"
    _description = "Journal Period"
    _order = "period_id"
    
    name = fields.Char('Journal-Period Name', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True, ondelete="cascade")
    period_id = fields.Many2one('account.period', 'Period', required=True, ondelete="cascade")
    active = fields.Boolean('Active', default=True, help="If the active field is set to False, it will allow you to hide the journal period without removing it.")
    state = fields.Selection([('draft','Draft'), ('printed','Printed'), ('done','Done')], 'Status', required=True, readonly=True, default='draft',
                            help='When journal period is created. The status is \'Draft\'. If a report is printed it comes to \'Printed\' status. When all transactions are done, it comes in \'Done\' status.')
    fiscalyear_id = fields.Many2one('account.fiscalyear',relation='period_id.fiscalyear_id',string='Fiscal Year', store=True)
    company_id = fields.Many2one('res.company',relation='journal_id.company_id', string='Company', store=True, readonly=True)
    
    
