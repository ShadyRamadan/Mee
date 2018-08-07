# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from openerp.osv import fields, osv
from openerp import models, fields, api, exceptions, tools 
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _name = "account.journal"
    _description = "Journal"
    _inherit = "account.journal"
    _order = 'sequence, type, code'

    type = fields.Selection([
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
            ('donation', 'Donation'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),
        ], required=True,
        help="Select 'Sale' for customer invoices journals."\
        " Select 'Purchase' for vendor bills journals."\
        " Select 'Donation' for donation journals."\
        " Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments."\
        " Select 'General' for miscellaneous operations journals."\
        " Select 'Opening/Closing Situation' for entries generated for new fiscal years.")