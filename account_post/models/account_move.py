# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from openerp.osv import fields, osv
from openerp import models, fields, api, exceptions, tools 
from openerp.tools.translate import _
from docutils.nodes import Invisible

_logger = logging.getLogger(__name__)

class AccountMove(osv.osv):
    _name = "account.move"
    _description = "Post"
    _inherit = "account.move"
    
    moveid = fields.Char(string='moveid', copy=False)
    moveid2 = fields.Char(string='moveid2', copy=False)
    #number2 = fields.Char(string='Number 2', store=True, copy=False)
    
    #@api.multi
    #@api.depends('name', 'state')
    #def name_get(self):
     #   if self.state == 'draft':
      #      if isinstance(self.id, models.NewId):
       #         self.number2 = '*' + str(self.id)
        #    else:
         #       self.number2 = '*' + str(self.id)
        #else:
         #   self.number2 = self.name               
        #return True
    
    @api.multi
    def post(self):
        invoice = self._context.get('invoice', False)
        self._post_validate()
        
        for move in self:
            self.env.cr.execute("SELECT count(id) FROM account_move_line where move_id = '%s'" %(move.id))
            res111 = self.env.cr.fetchone()[0]
            move.moveid = res111
            self.env.cr.execute("select count(*) from account_analytic_line inner join account_move_line as move_line on move_line.id = account_analytic_line.move_id where move_line.move_id= '%s'" %(move.id))
            res112 = self.env.cr.fetchone()[0]
            move.moveid2 = res112
            if res112 == 0:
                move.line_ids.create_analytic_lines()
            if move.name == '/':
                new_name = False
                journal = move.journal_id
                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            sequence = journal.refund_sequence_id
                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))

                if new_name:
                    move.name = new_name
        return self.write({'state': 'posted'})
    
class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _description = "Journal Item"
    _inherit = "account.move.line"
    
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')],related='move_id.state', string='Line State', store=True, copy=False)
    