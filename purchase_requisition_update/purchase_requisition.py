# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp import api, models, fields,osv
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError

_DESCRIPTION = [
    (1, 'عضو مالي'),
    (2, 'عضو فني'),
    (3, 'عضو مشتريات')
]

class purchase_requisition(models.Model):
    _name = "purchase.requisition"
    _description = "Purchase Requisition"
    _inherit = ['mail.thread', 'ir.needaction_mixin','purchase.requisition']

    #_columns = {
    #    'member_1': fields.many2one('hr.employee','First Member'),
     #   'member_2': fields.many2one('hr.employee','Second Member'),
      #  'member_3': fields.many2one('hr.employee','Third Member'),
       # 'member_4': fields.many2one('hr.employee','Fourth Member'),
        #'members_ids': fields.one2many('purchase.requisition.committee', 'requisition_id',
         #                      'Purchase Requisition Committee',
          #                     readonly=False,
           #                    copy=True,
            #                   track_visibility='onchange')
    #}
    members_ids =  fields.One2many('purchase.requisition.committee', 'requisition_id',
                               'Purchase Requisition Committee',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
    
class purchase_requisition_committee(models.Model):
    _name = "purchase.requisition.committee"
    _description = "Purchase Requisition Committee"
    
    requisition_id = fields.Many2one('purchase.requisition','Purchase Requisition',
                                 ondelete='cascade', readonly=True, invisible=False)
    member_id = fields.Many2one('hr.employee', 'Member Name',track_visibility='onchange')
    member_description = fields.Selection(selection=_DESCRIPTION)