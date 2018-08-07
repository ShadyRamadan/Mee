# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models, _
import urlparse, os
import datetime
import time
from datetime import datetime, timedelta
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp
    
_STATES = [
    (1, 'Draft'),
    (2, 'Sign In'),
    (3, 'Sign Out')
]

class fundraising_booths(models.Model):
    
    _name = 'fundraising.booths'
    _description = 'Fundraising Booths'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

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
    #color = fields.Integer('Color Index',compute="change_colore_on_kanban")
    @api.onchange('donation_section')
    def onchange_section(self):
        res = {}
        if self.donation_section:
            res['domain'] = {'donation_place': [('donation_section', '=', self.donation_section.id)]}
            return res
        
    donation_section = fields.Many2one('donation.section','Section', store=True, required=True, on_change="onchange_section(donation_section)")
    
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  compute="_get_default_employee")
    
    employee_user = fields.Many2one('res.users',
                                   'Employee User',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    
    department_id = fields.Many2one('hr.department', "Department", related="employee_id.department_id")
    
    state = fields.Selection(selection=_STATES,string='Attendance',index=True,default=1,
                         track_visibility='onchange',required=True,copy=False)
    
    donation_place = fields.Many2one('donation.place',string = 'Point', store=True)
    
    sign_in = fields.Datetime(
        string='Sign In DateTime', index=True,
        track_visibility='onchange')
    
    sign_out = fields.Datetime(
        string='Sign Out DateTime', index=True,
        track_visibility='onchange')
    
    worked_hours = fields.Float(string='Worked Hours')
    
    is_active = fields.Boolean(string="Active")
        
    donation_ids = fields.One2many(
        'donation.donation', 'fund_id', string='Donations',
        readonly=True)
    
    donation_count = fields.Integer(
        compute='_donation_count', string="# of Donations", readonly=True)
    
    @api.multi
    @api.depends('donation_ids.fund_id')
    def _donation_count(self):
        # The current user may not have access rights for donations
        for fund in self:
            try:
                fund.donation_count = len(fund.donation_ids)
            except:
                fund.donation_count = 0
                
    @api.multi
    def button_checkin(self):
        for rec in self:
            rec.state = 2
            rec.sign_in = datetime.now()
            rec.is_active = True
            action = 'sign_in'
            self.env.cr.execute("INSERT INTO hr_attendance (create_uid,employee_id,create_date,name,write_uid,write_date,action,worked_hours,department_id) VALUES ('%s','%s','%s','%s','%s','%s','%s','0.00','%s')" %(rec.employee_user.id,rec.employee_id.id,rec.sign_in,rec.sign_in,rec.employee_user.id,rec.sign_in,action,rec.department_id.id))  
        return True
    
    @api.multi
    def button_checkout(self):
        for rec in self:
            rec.state = 3
            sign_out = datetime.now()
            rec.sign_out= datetime.now()
            rec.is_active = False
            action = 'sign_out'
            last_signin_datetime = datetime.strptime(rec.sign_in, '%Y-%m-%d %H:%M:%S')
            signout_datetime = datetime.strptime(rec.sign_out, '%Y-%m-%d %H:%M:%S')
            workedhours_datetime = (signout_datetime - last_signin_datetime)
            worked_hours = ((workedhours_datetime.seconds) / 60) / 60.0
            rec.worked_hours = worked_hours
            output = round(worked_hours,2)
            self.env.cr.execute("INSERT INTO hr_attendance (create_uid,employee_id,create_date,name,write_uid,write_date,action,worked_hours,department_id) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s')" %(rec.employee_user.id,rec.employee_id.id,rec.sign_out,rec.sign_out,rec.employee_user.id,rec.sign_out,action,output,rec.department_id.id))
        return True
   
    #def change_colore_on_kanban(self):   
     #   for record in self:
      #      if record.state == 1:
       #         record.color = 3
        #    elif record.state == 2:
         #       record.color = 5
          #  elif record.state == 3:
           #     record.color = 6