# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class DonationVmachine(models.Model):
    _name = 'donation.vmachine'
    _description = 'Code attributed for a Donation Visa Machine'
    _order = 'code'
    _rec_name = 'code'

    @api.multi
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.code:
                name = u'[%s] %s' % (camp.code, name)
            camp.display_name = name

    code = fields.Char(string='Code', size=10, required=True)
    name = fields.Char(string='Name')
    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name',
        readonly=True, store=True)
    bank_id = fields.Many2one(
        'res.bank', string = 'Bank'
    )
    donation_section = fields.Many2one('donation.section','Section', store=True)
    donation_method = fields.Many2one('donation.instrument','Method', store=True)
    #tag_id = fields.Many2one('account.analytic.tag',string='Tag',store=True)
    #analytic_account_id = fields.Many2one(
     #   'account.analytic.account', string='Analytic Account',
      #  domain=[('account_type', '!=', 'closed')], ondelete='restrict')
    #account_id = fields.Many2one(
     #   'account.account', string='Account Name',
      #  domain="[('deprecated', '=', False), ('x_level', '=', 5)]", ondelete='restrict')
    responsible = fields.Many2one('res.users',
                                   'Responsible by',
                                   track_visibility='onchange')
    nota = fields.Text(string='Notes')
    
    _sql_constraints = [
            ('display_name_uniq', 'UNIQUE (name)',  'This Visa Machine already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Visa Machine Code already exists')
        ]