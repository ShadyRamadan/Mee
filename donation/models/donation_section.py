# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class DonationSection(models.Model):
    _name = 'donation.section'
    _description = 'Code attributed for a Donation Section'
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
    tag_id = fields.Many2one('account.analytic.tag',string='Tag',store=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        domain=[('account_type', '!=', 'closed')], ondelete='restrict')
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True,
        domain=[
            ('type', 'in', ('bank', 'cash')),
            ('allow_donation', '=', True)],
        track_visibility='onchange')
    responsible = fields.Many2one('res.users','Responsibility',track_visibility='onchange')
    nota = fields.Text(string='Notes')
    
    _sql_constraints = [
            ('display_name_uniq', 'UNIQUE (name)',  'This Campaign already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Campaign Code already exists')
        ]