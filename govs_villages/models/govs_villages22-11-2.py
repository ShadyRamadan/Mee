# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from openerp import api, fields, models, osv
import urlparse, os
import datetime
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
import openerp.addons.decimal_precision as dp

class gov(models.Model):
    _description = "gov"
    _name = 'govs.villages.gov'
    #_columns = {
    #    'country_id': fields.many2one('res.country', 'Country', required=True),
    #    'name': fields.char('Gov Name', required=True,
    #                        help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton'),
    #    'code': fields.char('Gov Code', size=3,
    #                        help='The state code in max. three chars.', required=True),
    #    'city_ids': fields.one2many('govs.villages.city', 'city_id', string='Cities'),
    #}
    # journal_id = fields.Many2one('account.journal', string=
    def _gov(self):
        for data in self:
            if data.state_id :
                data.name = data.state_id.name
        
    country_id = fields.Many2one('res.country', 'الدولة', required=True, default=66)
    #state_id = fields.Many2one('res.country.state', 'المحافظة', required=True)
    name = fields.Char('اسم المحافظة', required=False)
    gov_en_id = fields.Many2one('govs.villages.enggov',string='Governorate Name', required=True)
    code = fields.Char('كود المحافظة', size=10, required=False)
    tag_id = fields.Many2one('account.analytic.tag',string='Tag',store=True)
    city_ids = fields.One2many('govs.villages.city', 'gov_id', string='المركز / المدينة')
    _order = 'code'
    _sql_constraints = [
            ('name_uniq', 'UNIQUE (name)',  'This Governorate Arabic Name already exists'),
            ('english_name_uniq', 'UNIQUE (gov_en_id)',  'This Governorate English Name already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Governorate Code already exists')
        ]


class city(models.Model):
    _description = "city"
    _name = 'govs.villages.city'
    #_columns = {
    #    'country_id': fields.many2one('res.country', 'Country', required=True),
    #    'gov_id': fields.many2one('govs.villages.gov', 'Gov', required=True),
    #    'name': fields.char('City/Center Name', required=True,
    #                        help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton'),
    #    'code': fields.char('City Code', size=4,
    #                        help='The state code in max. four chars.', required=True),
    #    'village_ids': fields.one2many('govs.villages.village', 'village_id', string='Villages'),
    #}
    country_id = fields.Many2one('res.country', 'الدولة', required=True, default=66)
    gov_id = fields.Many2one('govs.villages.gov', 'المحافظة', required=True)
    #state_id = fields.Many2one('res.country.state', 'State', required=True)
    name = fields.Char('اسم المركز/المدينة', required=True)
    city_en_id = fields.Many2one('govs.villages.engcity',string='City Name', required=True)
    code = fields.Char('كود المركز/المدينة', size=10, required=False)
    village_ids = fields.One2many('govs.villages.village', 'city_id', string='القري/المناطق')
    _order = 'code'
    
    _sql_constraints = [
            ('name_uniq', 'UNIQUE (name)',  'This City Name already exists'),
            ('english_name_uniq', 'UNIQUE (city_en_id)',  'This City English Name already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This City Code already exists')
        ]

class village(models.Model):
    _description = "Village"
    _name = 'govs.villages.village'
    #_columns = {
    #    'country_id': fields.many2one('res.country', 'Country', required=True),
    #    'gov_id': fields.many2one('govs.villages.gov', 'Gov', required=True),
    #    'city_id': fields.many2one('govs.villages.city', 'City', required=True),
    #    'name': fields.char('Village/district Name', required=True,
    #                        help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton'),
    #    'code': fields.char('Village Code', size=4,
    #                        help='The state code in max. four chars.', required=True),
    #}
    #@api.model
    #def _get_default_country(self):
     #   return self.env['res.users'].browse(self.env.uid)
    @api.onchange('gov_id')
    def onchange_gov(self):
        res = {}
        if self.gov_id:
            res['domain'] = {'city_id': [('gov_id', '=', self.gov_id.id)]}
            return res
    
    #def onchange_gov(self,cr, uid, ids, gov_id, context=None):
    #    res = {}
    #    if self.gov_id: #on old api it will return id, instead of record
    #        res['domain'] = {'city_id': [('gov_id', '=', self.gov_id)]}
    #        return res

    country_id = fields.Many2one('res.country', 'الدولة', required=True, default=66)
    gov_id = fields.Many2one('govs.villages.gov', 'المحافظة', required=True, on_change="onchange_gov(gov_id)")
    city_id = fields.Many2one('govs.villages.city', 'المركز/المدينة', required=True)
    #state_id = fields.Many2one('res.country.state', 'State', required=True)
    name = fields.Char('القرية/المنطقة', required=True)
    village_en_id = fields.Many2one('govs.villages.engvillage',string='Village Name', required=True)
    code = fields.Char('كود القرية/المنطقة', size=10, required=False)
    _order = 'code'
    
    _sql_constraints = [
            ('name_uniq', 'UNIQUE (name)',  'This Village Name already exists'),
            ('english_name_uniq', 'UNIQUE (village_en_id)',  'This City English Name already exists'),
            ('code_uniq', 'UNIQUE (code)',  'This Village Code already exists')
        ]
    
    class eng_gov(models.Model):
        _description = "gov"
        _name = 'govs.villages.enggov'
        
        name = fields.Char('Governorate Name', required=False)
    
    class eng_city(models.Model):
        _description = "gov"
        _name = 'govs.villages.engcity'
        
        name = fields.Char('city Name', required=False)
        
    class eng_village(models.Model):
        _description = "gov"
        _name = 'govs.villages.engvillage'
        
        name = fields.Char('Village Name', required=False)