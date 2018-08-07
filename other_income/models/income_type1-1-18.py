# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api

_STATES = [
    (1, 'Prep Insurance'),
    (2, 'Final Insurance'),
    (3, 'Conditions Booklets'),
    (4, 'Interest'),
    (5, 'Change Rate'),
    (6, 'Acquired Discounts'),
    (7, 'Others')
]

class DonationSection(models.Model):
    _name = 'income.type'
    _description = 'Income Type'
    _order = 'code'
    _rec_name = 'display_name'

    @api.multi
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.code:
                name = u'[%s] %s' % (camp.code, name)
            camp.display_name = name

    code = fields.Char(string='Code', size=10)
    name = fields.Char(string='Name', required=True)
    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name',
        readonly=True, store=True)
    
    journal_id = fields.Many2one('account.journal', string='Journal',
        domain=[('type', 'in', ('bank', 'cash')),
            ('allow_donation', '=', True)],track_visibility='onchange')
    
    account_id = fields.Many2one('account.account', string='Account Name',
        domain="[('deprecated', '=', False), ('x_level', '=', 5)]", ondelete='restrict')
    
    responsible = fields.Many2one('res.users','Responsible by',track_visibility='onchange')
    
    state = fields.Selection(selection=_STATES,string='Status',index=True,
                             track_visibility='onchange',copy=False)
    
    #is_insurance = fields.Boolean(string='Prep/Final Insurance')
    #is_interest = fields.Boolean(string='Interest')
    #is_change_rate_profits = fields.Boolean(string='Change Rate Profits')
    #is_change_rate_losses = fields.Boolean(string='Change Rate Losses')
    #is_acquired_discounts = fields.Boolean(string='Acquired Discounts')
    #is_conditions_booklets = fields.Boolean(string='Conditions Booklets')
    
    nota = fields.Text(string='Notes')
    
    _sql_constraints = [
            ('display_name_uniq', 'UNIQUE (name)',  'This Type Name already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Type Code already exists')
        ]