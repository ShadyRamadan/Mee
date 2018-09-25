# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _name = "account.move"
    _inherit = "account.move"
    
    period_id = fields.Many2one('account.period', string='Period', required=True, states={'posted': [('readonly', True)]})