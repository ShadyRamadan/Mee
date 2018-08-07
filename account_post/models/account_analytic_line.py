# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from openerp.osv import fields, osv
from openerp import models, fields, api, exceptions, tools 
from openerp.tools.translate import _
from docutils.nodes import Invisible

_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _description = 'Analytic Line'
    _inherit = "account.analytic.line"
    
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], related='move_id.state', string='Analytic State', store=True, copy=False)