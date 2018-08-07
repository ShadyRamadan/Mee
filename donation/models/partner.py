# -*- coding: utf-8 -*-
# © 2014-2016 Barroux Abbey (http://www.barroux.org)
# © 2014-2016 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api

_CLASSIFICATION = [
    (1, 'Class A'),
    (2, 'Class B'),
    (3, 'Class C')
] 

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _rec_name = "display_name"
    
    @api.multi
    @api.depends('donation_line_ids_partner.partner_id')
    def _donation_count(self):
        # The current user may not have access rights for donations
        for partner in self:
            try:
                partner.donation_count = len(partner.donation_line_ids_partner)
            except:
                partner.donation_count = 0
                
    @api.multi
    @api.depends('name', 'mobile')
    def _compute_display_name(self):
        for camp in self:
            name = camp.name
            if camp.mobile:
                name = u'%s [%s] ' % (name, camp.mobile)
            camp.display_name = name
                
    @api.multi
    @api.depends('donation_line_ids_partner.amount')          
    def _compute_total(self):
        for partner in self:
            if partner.is_donor == True:
                for line in partner.donation_line_ids_partner:
                    partner.amount_total += line.amount
            else:
                partner.amount_total == 0
    
    @api.multi
    @api.depends('amount_total','donation_count')          
    def _compute_classification(self):
        for partner in self:
            if partner.is_donor == True and partner.donation_count != 0:
                donation_average = partner.amount_total / partner.donation_count
                partner.donation_average = donation_average
                if donation_average < 1000:
                    partner.donor_classification = 3
                elif donation_average >= 1000 and donation_average < 20000:
                    partner.donor_classification = 2
                elif donation_average >= 20000:
                    partner.donor_classification = 1
            
    @api.multi
    @api.depends('donation_line_ids.donation_collector')
    def _collection_count(self):
        # The current user may not have access rights for donations
        for collector in self:
            try:
                collector.collection_count = len(collector.donation_line_ids)
            except:
                collector.collection_count = 0
                
    display_name = fields.Char(string='Display Name', compute='_compute_display_name',readonly=True, store=True)
    
    donation_ids = fields.One2many(
        'donation.donation', 'partner_id', string='Donations',
        readonly=True)
    
    donation_line_ids_partner = fields.One2many(
        'donation.line', 'partner_id', string='Donations',
        readonly=True)
    
    donation_line_ids = fields.One2many(
        'donation.line', 'donation_collector', string='Collections',
        readonly=True)
    
    amount_total = fields.Float(
        compute='_compute_total', string='Amount Total')  
    
    donation_average = fields.Float(
        compute='_compute_classification', string='Donation Average')
    
    donation_count = fields.Integer(
        compute='_donation_count', string="# of Donations", readonly=True)
    
    collection_count = fields.Integer(
        compute='_collection_count', string="# of Collections", readonly=True)
    
    is_donor = fields.Boolean(string="Donor")
    
    is_collector = fields.Boolean(string="Collector")
    
    donor_classification = fields.Selection(selection=_CLASSIFICATION, string = 'Classification',compute='_compute_classification' )
    
    _sql_constraints = [
            ('name_uniq', 'UNIQUE (name,is_donor)',  'Donor already exists')
        ]
    
    _sql_constraints = [
            ('name_uniq', 'UNIQUE (name,is_collector)',  'Collector already exists')
        ]
