# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
from openerp.tools import float_is_zero, float_compare
import openerp.addons.decimal_precision as dp

#class DonationDonation(models.Model):
 #   _name = 'donation.donation'
  #  _description = 'Donation'
   # _inherit = "donation.donation"

class Donation(models.Model):
    _name = 'donation.donation'
    _description = 'Donations'
    _inherit = "donation.donation"
    
    fund_id = fields.Many2one(
        'fundraising.booths' , string='Fund-raising No.',copy=True,store=True)
    
    box_id = fields.Many2one(
        'fundraising.boxes' , string='Box No.',copy=True,store=True)