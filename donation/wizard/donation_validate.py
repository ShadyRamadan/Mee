# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields


class DonationValidate(models.TransientModel):
    _name = 'donation.validate'
    _description = 'Validate Donations'

    @api.multi
    def run(self):
        assert self.env.context.get('active_model') == 'donation.donation',\
            'Source model must be donations'
        assert self.env.context.get('active_ids'), 'No donations selected'
        donations = self.env['donation.donation'].browse(
            self.env.context.get('active_ids'))
        donations.validate()
        return
    
    @api.multi
    def approve(self):
        assert self.env.context.get('active_model') == 'donation.donation',\
            'Source model must be donations'
        assert self.env.context.get('active_ids'), 'No donations selected'
        donations = self.env['donation.donation'].browse(
            self.env.context.get('active_ids'))
        donations.transfer()
        return


class DonationBank(models.TransientModel):
    _name = 'donation.bank'
    _description = 'Donations To-Bank'

    @api.multi
    def run(self):
        assert self.env.context.get('active_model') == 'donation.line',\
            'Source model must be donations Lines'
        assert self.env.context.get('active_ids'), 'No donations selected'
        donations_line = self.env['donation.line'].browse(
            self.env.context.get('active_ids'))
        for donation in self:
            for line in donations_line:
                self.env.cr.execute("UPDATE donation_line set journal_id= '%s' where id= '%d'" %(donation.journal_id.id,line.id))
                self.env.cr.execute("UPDATE donation_line set account_id_bank= '%s' where id= '%d'" %(donation.account_id_bank.id,line.id))
        donations_line.to_bank()
        
        return
    
    

    journal_id =  fields.Many2one('account.journal',
        domain=[
            ('type', 'in', ('bank', 'cash')),
            ('allow_donation', '=', True)],
        track_visibility='onchange')
    account_id_bank = fields.Many2one('account.account', string='Bank Account', store=True)
    
    
    
    #@api.multi
    #def approve(self):
     #   assert self.env.context.get('active_model') == 'donation.donation',\
      #      'Source model must be donations'
       # assert self.env.context.get('active_ids'), 'No donations selected'
        #donations = self.env['donation.donation'].browse(
         #   self.env.context.get('active_ids'))
        #donations.transfer()
        #return