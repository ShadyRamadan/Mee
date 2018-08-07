# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
from openerp.tools import float_is_zero, float_compare
import openerp.addons.decimal_precision as dp

_MEDICALDEVICES = [
    (1, 'جهاز الحضانات'),
    (2, ' جهاز فوتو'),
    (3, 'مستلزمات أبو الريش')
] 

#class DonationDonation(models.Model):
 #   _name = 'donation.donation'
  #  _description = 'Donation'
   # _inherit = "donation.donation"

  


class DonationLine(models.Model):
    _name = 'donation.line'
    _description = 'Donation Lines'
    _rec_name = 'recipt_number'
    _inherit = "donation.line"
    
    feedback_ids = fields.One2many(
        'donation.feedback', 'donation_line_id', string='Donation Feedbacks',copy=True)

class DonationFeedback(models.Model):
    _name = 'donation.feedback'
    _description = 'Donation Feedback'
    
    donation_line_id = fields.Many2one(
        'donation.line', string='Donation Line', ondelete='cascade')
    feedback_project = fields.Many2one('project.project', store=True, string='Project')
    feedback_date = fields.Date(
        string='Feedback Date',default=fields.Date.context_today, index=True,
        track_visibility='onchange')
    grantee_name = fields.Many2one('needed.cases', store=True, string='Grantee')
    medical_devices = fields.Selection(selection=_MEDICALDEVICES,store=True, string='Medical Devices')
    
class crm_lead(models.Model):
    """ CRM Lead Case """
    _name = "crm.lead"
    _description = "Lead/Opportunity/Follow Up"
    _inherit = "crm.lead"
    
    type = fields.Selection(
            [('lead', 'Lead'), ('opportunity', 'Opportunity'), ('follow_up', 'Follow Up')],
            string='Type', select=True, required=True,
            help="Type is used to separate Leads and Opportunities")
    donation_line_id = fields.Many2one('donation.line',string='Recipt Number', size=32)



class crm_stage(models.Model):
    """ CRM Stage Case """
    _name = "crm.stage"
    _description = "Lead/Opportunity/Follow Up"
    _inherit = "crm.stage"
    
    type = fields.Selection([('lead', 'Lead'), ('opportunity', 'Opportunity'), ('both', 'Both'), ('follow_up', 'Follow Up')],
                                 string='Type', required=True,
                                 help="This field is used to distinguish stages related to Leads from stages related to Opportunities, or to specify stages available for both types.")
