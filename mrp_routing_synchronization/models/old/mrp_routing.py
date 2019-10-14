# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from email.policy import default
_logger = logging.getLogger(__name__)

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    
    ref_id = fields.Integer(string='Ref.', readonly=True, default=-1)
    
class QualityPoint(models.Model):
    _inherit = 'quality.point'
        
    ref_id = fields.Integer(string='Ref.', readonly=True, default=-1)
    

class MrpRouting(models.Model):
    _inherit = 'mrp.routing'
    
    @api.multi
    def copy(self, default=None):
        res =  super(MrpRouting, self).copy(default)
        for operation in res.operation_ids:
            origine= self.env['mrp.routing.workcenter'].search([('name', '=', operation.name), ('routing_id', '=', self.id)], limit=1)
            operation.write({'ref_id': origine.id})
        for quality_point in res.quality_point_ids:
            origine_point= self.env['quality.point'].search([('title', '=', quality_point.title), ('routing_id', '=', self.id)], limit=1)
            quality_point.write({'ref_id': origine_point.id})
        return res
    
    #-------------Routing Workcenter-------------------#
    @api.multi
    def write_create_routing_workcenter(self):
        for line in self.operation_ids:
            child_lines = self.env['mrp.routing.workcenter'].search([('ref_id', '=', line.id), ('routing_id.parent_id', '=', self.id)])
            if child_lines:
                for child_line in child_lines:
                    child_line.write({
                        'name': line.name,
                        'workcenter_id': line.workcenter_id.id,
                        'product_tmpl_id': line.product_tmpl_id.id,
                        'expertise': line.expertise,
                        'batch': line.batch,
                        'batch_size':line.batch_size,
                        'note': line.note,
                        'worksheet': line.worksheet,
                        })
            for child in self.child_ids:
                child_line_exist = self.env['mrp.routing.workcenter'].search([('ref_id', '=', line.id), ('routing_id', '=', child.id)])
                if not child_line_exist and not self.env['quality.point'].search([('operation_id', '=', line.id), ('routing_id', '=', self.id)]):
                    default=None
                    default = dict(default or {})
                    default.update({
                        'ref_id': line.id,
                        'routing_id': child.id,      
                        })
                    line.copy(default)
    
    @api.multi
    def delete_routing_workcenter(self):
        for childs in self.child_ids:
            child_lines = self.env['mrp.routing.workcenter'].search([('routing_id', '=', childs.id), ('ref_id', '!=', -1)])
            for refs in child_lines:
                list = self.env['mrp.routing.workcenter'].search([('routing_id', '=', self.id), ('id', '=', refs.ref_id)])
                if not list:
                    refs.unlink()
                    
                    
    #-------------Quality Point-------------------#
    @api.multi
    def write_create_quality_point(self):
        for line in self.quality_point_ids:
            child_lines = self.env['quality.point'].search([('ref_id', '=', line.id), ('routing_id.parent_id', '=', self.id)])
            
            
            existe=False
            for child in self.child_ids:
                child_line_exist = self.env['quality.point'].search([('ref_id', '=', line.id), ('routing_id', '=', child.id)])
                if child_line_exist:
                    existe=True
                    child_line_exist.write({
                        'title': line.title,
                        'product_tmpl_id': line.product_tmpl_id.id,
                        'picking_type_id': line.picking_type_id.id,
                        #'routing_id': line.routing_id.id,
                        #'operation_id': line.operation_id.id,
                        'measure_frequency_type': line.measure_frequency_type,
                        'measure_frequency_value': line.measure_frequency_value,
                        'test_type_id':line.test_type_id.id,
                        'norm': line.norm,
                        'norm_unit': line.norm_unit,
                        'tolerance_min': line.tolerance_min,
                        'tolerance_max': line.tolerance_max,
                        'team_id': line.team_id.id,
                        'user_id': line.user_id.id,
                        'worksheet': line.worksheet,
                        'worksheet_page': line.worksheet_page,
                        'note': line.note,
                        'reason': line.reason,
                        'failure_message': line.failure_message
                        })
                if not existe :
                    default=None
                    default = dict(default or {})
                    operation = line.operation_id
                    child_operations = self.env['mrp.routing.workcenter'].search([('ref_id', '=', operation.id), ('routing_id', '=', child.id)], limit=1)
                    if child_operations:
                        qualite = line.copy(default)
                        qualite.write({
                            'ref_id': line.id,
                            'routing_id': child.id,   
                            'operation_id':  child_operations.id
                        })
                    else:
                        default2=None
                        default2 = dict(default2 or {})
                        default2.update({
                            'ref_id': line.operation_id.id,
                            'routing_id': child.id, 
                            })
                        op = operation.copy(default2)                        
                        search_ids = self.env['quality.point'].search([('operation_id', '=', op.id), ('routing_id', '=', child.id)])
                        last_id = search_ids and max(search_ids)                        
                        last_id.write({
                            'ref_id': line.id
                        })
    
    @api.multi
    def delete_quality_point(self):
        for childs in self.child_ids:
            child_lines = self.env['quality.point'].search([('routing_id', '=', childs.id), ('ref_id', '!=', -1)])
            for refs in child_lines:
                list = self.env['quality.point'].search([('routing_id', '=', self.id), ('id', '=', refs.ref_id)])
                if not list:
                    refs.unlink()
    
    @api.multi
    def childs_synchronisation(self):
               
        self.delete_quality_point()   
        self.write_create_quality_point()
        
        self.delete_routing_workcenter()
        self.write_create_routing_workcenter()
        
    
    

