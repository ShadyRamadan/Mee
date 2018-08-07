# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models, _
import urlparse, os
import datetime
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp
    
_STATES = [
    (1, 'Draft'),
    (2, 'Start'),
    (3, 'Revoke'),
    (4,'Open'),
    (5,'Finish')
]

class fundraising_boxes(models.Model):
    
    _name = 'fundraising.boxes'
    _description = 'Fund-raising Boxes'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'id'

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)
    
    @api.onchange('employee_user')
    def _get_default_employee(self):
        for rec in self:
            requested_by = rec.employee_user.id
        #self.employee_id = 
            rec.env.cr.execute("SELECT count(hr_employee.id) FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(rec.employee_user.id))
            res0 = rec.env.cr.fetchone()[0]
            if (res0 > 0):
                rec.env.cr.execute("SELECT hr_employee.id FROM hr_employee inner join resource_resource on hr_employee.resource_id = resource_resource.id where user_id ='%s'"  %(rec.employee_user.id))
                res = rec.env.cr.fetchone()[0]
                rec.employee_id = res

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  compute="_get_default_employee")
    
    employee_user = fields.Many2one('res.users',
                                   'User',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    
    responsible_employee = fields.Many2one('hr.employee', string='Responsible Employee')
    
    state = fields.Selection(selection=_STATES,string='State',index=True,default=1,
                         track_visibility='onchange',required=True,copy=False)
    
    box_code = fields.Many2one('donation.box',string='Box Code',store=True)
    
    start_date = fields.Datetime(string='Start Date', index=True,track_visibility='onchange')
    revoke_date = fields.Datetime(string='Revoke Date', index=True,track_visibility='onchange')
    open_date = fields.Datetime(string='Open Date', index=True,track_visibility='onchange')
    donation_place = fields.Many2one('donation.place',string = 'Point', store=True)
    #partner_id = fields.Many2one('res.partner','recipient name',required=True)
    is_active = fields.Boolean(string="Active")
    
    donation_ids = fields.One2many(
        'donation.donation', 'box_id', string='Donations',
        readonly=True)
    
    donation_count = fields.Integer(
        compute='_donation_count', string="# of Donations", readonly=True)
    
    @api.multi
    @api.depends('donation_ids.box_id')
    def _donation_count(self):
        # The current user may not have access rights for donations
        for box in self:
            try:
                box.donation_count = len(box.donation_ids)
            except:
                box.donation_count = 0
        
    @api.multi
    def button_start(self):
        for rec in self:
            rec.state = 2
            rec.start_date = datetime.datetime.now()
            rec.is_active = True
        return True
    
    @api.multi
    def button_revoke(self):
        for rec in self:
            rec.state = 3
            rec.revoke_date = datetime.datetime.now()
            rec.is_active = False
        return True
    
    @api.multi
    def button_open(self):
        for rec in self:
            rec.state = 4
            rec.open_date = datetime.datetime.now()
        return True