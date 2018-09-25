# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models


class account_period_close(models.TransientModel):
    """
        close period
    """
    _name = "account.period.close"
    _description = "period close"
    
    sure = fields.Boolean('Check this box')
    
    @api.multi
    def run(self):
        
        donations.validate()
        return
    
    
    def data_save(self):

        journal_period_pool = self.pool.get('account.journal.period')
        period_pool = self.pool.get('account.period')
        account_move_obj = self.pool.get('account.move')
        
        assert self.env.context.get('active_model') == 'account.period',\
            'Source model must be Periods'
        assert self.env.context.get('active_ids'), 'No periods selected'
        periods = self.env['account.period'].browse(self.env.context.get('active_ids'))
        
        
        mode = 'done'
        for form in self:
            if form.sure == True:
                #for id in self:
                form.env.cr.execute('update account_journal_period set state=%s where period_id=%s', (mode, periods.id))
                form.env.cr.execute('update account_period set state=%s where id=%s', (mode, periods.id))
        return {'type': 'ir.actions.act_window_close'}