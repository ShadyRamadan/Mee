#from odoo import api, fields, models, _
from openerp import models, fields, api, _
import datetime
from datetime import date, datetime
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
import urlparse, os
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap

import openerp.addons.decimal_precision as dp

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)

class crossovered_budget(models.Model):
    _name = "crossovered.budget"
    _description = "Budget"
    _inherit = ['mail.thread','crossovered.budget']
    _rec_name = "display_name"
    
            
    budget_fundstream = fields.Many2one('donation.fundstream',string='Fundstream')
    
    
    @api.multi
    @api.depends('crossovered_budget_line.planned_amount')
    def _compute_amount_all(self):
        for budget in self:
            fund1 = 0
            fund2 = 0
            fund3 = 0
            fund4 = 0
            for line in budget.crossovered_budget_line: 
                budget.total_cost += line.planned_amount
            if isinstance(self.id, models.NewId):
                    fund = 0
            else:
                if self.budget_fundstream:   
                    fund1 = budget.total_cost
                    self.env.cr.execute("select total_other from donation_fundstream  where id ='%s'" %(budget.budget_fundstream.id))
                    fund2 = self.env.cr.fetchone()[0]
                    self.env.cr.execute("select total_fund from donation_fundstream  where id ='%s'" %(budget.budget_fundstream.id))
                    fund3 = self.env.cr.fetchone()[0]
                    if isinstance(fund2, float) and isinstance(fund3, float):
                        fund4 = (fund2+fund3) - fund1
                    elif isinstance(fund2, float):
                        fund4 =  (fund2) - fund1 
                    elif isinstance(fund3, float):
                        fund4 =  (fund3) - fund1 
                    else:
                        fund4 = - fund1
               
                    self.env.cr.execute("update donation_fundstream set difference = '%s' where id ='%s'" %(fund4,budget.budget_fundstream.id))
                    self.env.cr.execute("update donation_fundstream set cost_budget = '%s' where id ='%s'" %(fund1,budget.budget_fundstream.id))

                #if fund1 > 0:
                 #   if fund4 > 0:
                  #      self.env.cr.execute("update donation_fundstream set fund_active = 'True' where id ='%s'" %(budget.budget_fundstream.id))
                   # else:
                    #    self.env.cr.execute("update donation_fundstream set fund_active = 'False' where id ='%s'" %(budget.budget_fundstream.id))
                #else:
                  #  self.env.cr.execute("update donation_fundstream set fund_active = 'False' where id ='%s'" %(budget.budget_fundstream.id))