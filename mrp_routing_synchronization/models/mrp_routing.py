# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
import logging
from email.policy import default
_logger = logging.getLogger(__name__)

    

class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    ### ADDING ###
    quality_point_ids = fields.One2many(comodel_name='quality.point', inverse_name='routing_id', string='Quality Point')
    parent_id = fields.Many2one(comodel_name='mrp.routing', string='Parent', readonly=True)
    child_ids = fields.One2many(comodel_name='mrp.routing', inverse_name='parent_id', string='Child', readonly=False)
    child_count = fields.Integer(compute='_compute_child_count', string='# Child')
    last_synchronization = fields.Datetime(string='Last synchronization', readonly=True)
    is_sync = fields.Boolean(string='Is synchronized', compute='_compute_sync')
    to_sync = fields.Boolean(string='Must be synchronize', compute='_compute_to_sync')
    bom_ids = fields.One2many(comodel_name='mrp.bom', compute='_compute_bom_ids')
    product_ids = fields.One2many(comodel_name='product.template', compute='_compute_bom_ids')

    @api.multi
    def _compute_bom_ids(self):
        for record in self:
            record.bom_ids = self.env['mrp.bom'].search([('routing_id', '=', record.id)])
            record.product_ids = record.bom_ids.mapped('product_tmpl_id')


    ### COMPUTE ###
    @api.depends('child_ids')
    @api.multi
    def _compute_child_count(self):
        """
        calculate number of children
        :return: int
        """
        for record in self:
            record.child_count = len(record.child_ids) if record.child_ids else 0


    @api.depends('last_synchronization', 'parent_id', 'child_ids')
    @api.multi
    def _compute_sync(self):
        """
        check if parent/children are synchronized
        :return:
        """
        for record in self:
            # _logger.warning("_compute_sync: %r", record.id)
            if record._is_child():
                record.is_sync = True if record.last_synchronization == record.parent_id.last_synchronization else False
            elif record._is_parent():
                # record.is_sync = True if all(record.child_ids.filtered(lambda x: x.last_synchronization == record.last_synchronization)) else False
                record.is_sync = True if all(x == record.last_synchronization for x in record.child_ids.mapped('last_synchronization')) else False
            else:
                record.is_sync = False


    @api.depends('last_synchronization', 'write_date')
    @api.multi
    def _compute_to_sync(self):
        """
        check if routing has edited from last synchronization
        :return:
        """
        for record in self:
            if record._is_parent():
                record.to_sync = True if record.write_date != record.last_synchronization else False
            else:
                record.to_sync = False


    ### ACTION ###

    @api.multi
    def action_quality_point_update(self):
        for record in self:
            if len(record.product_ids) == 1 and len(record.bom_ids) == 1 and record.quality_point_ids:
                product_id = record.product_ids[-1]
                record.quality_point_ids.write({
                    'product_tmpl_id': product_id.id,
                    'product_id': product_id.product_variant_id.id,
                })

        return True


    @api.multi
    def action_view_child(self):
        """
        mrp routing treeview (child)
        :return: action
        """
        self.ensure_one()
        action = self.env.ref("mrp.mrp_routing_action").read()[0]
        action['domain'] = [('id', 'in', self.child_ids.ids)]
        action['context'] = {'create': False}
        return action


    @api.multi
    def action_sync(self):
        """
        Synchronize operations and quality points to children
        :return: bool
        """
        for record in self:
            now = datetime.now()

            record._sync_operation()
            record._sync_quality_point()

            # update synchronization date
            record.update({'last_synchronization': now})
            record.child_ids.update({'last_synchronization': now})

        return True


    @api.multi
    def action_delete_relationship(self):
        """
        Remove parent relationship and fix ref_id on operations and quality points
        :return: bool
        """
        for record in self:
            record.update({'parent_id': False})
            if any(record.operation_ids.filtered(lambda x: x.ref_id != -1)):
                record.operation_ids.update({'ref_id': -1})
                record.quality_point_ids.update({'ref_id': -1})

        return True


    ### OVERRIDE ###
    @api.multi
    def copy(self, default=None):
        """
        Add suffix to routing name and set parent on new record
        :param default:
        :return: recordset
        """
        self.ensure_one()
        chosen_name = default.get('name') if default else ''
        new_name = chosen_name or _('%s (copy)') % self.name
        default = dict(default or {}, name=new_name, parent_id=self.id)
        res = super(MrpRouting, self).copy(default)

        # fix ref_id on new operations
        for child, parent in zip(res.operation_ids, self.operation_ids):
            child.update({'ref_id': parent.id})

        # fix ref_id on new quality points
        for child, parent in zip(res.quality_point_ids, self.quality_point_ids):
            child.update({'ref_id': parent.id})

        return res


    @api.multi
    def _is_child(self):
        """
        check if current recordset is a child
        :return: bool
        """
        self.ensure_one()
        return bool(self.parent_id and not self.child_ids)


    @api.multi
    def _is_parent(self):
        """
        check if current recordset is an ancestor
        :return: bool
        """
        self.ensure_one()
        return bool(not self.parent_id and self.child_ids)


    @api.multi
    def _sync_quality_point(self):
        """
        1. remove motherless quality points (withnot new ref_id)
        2. udpate all chidren's quality points
        3. create all missings quality points by duplicate them
        :return: bool
        """
        for record in self:

            # remove motherless quality points
            child_quality_point_to_delete = record.child_ids.mapped('quality_point_ids').filtered(lambda x: x.ref_id != -1 and x.ref_id not in record.quality_point_ids.ids)
            # _logger.warning('[SYNC] remove motherless operations: %r' % (child_quality_point_to_delete.ids))
            child_quality_point_to_delete.unlink()

            # update all children's quality points
            for quality_point in record.quality_point_ids:
                to_update = record.child_ids.mapped('quality_point_ids').filtered(lambda x: x.ref_id == quality_point.id)
                # _logger.warning('[SYNC] update all child quality points: %r' % (to_update.ids))
                to_update.update(quality_point._prepare_child_vals())

            # create (by copy) all missing operations from parent
            for child in record.child_ids:
                missing_quality_points = record.quality_point_ids.filtered(lambda x: x.id not in child.quality_point_ids.mapped('ref_id'))
                # _logger.warning('[SYNC] create missing quality points: %r' % (missing_quality_points.ids))

                for quality_point in missing_quality_points:
                    child_operation = child.operation_ids.filtered(lambda x: x.ref_id == quality_point.operation_id.id)
                    if not child_operation:
                        # _logger.error('[SYNC] error, operation not found for quality point: %r' % (quality_point))
                        continue

                    new_quality_point = quality_point.copy({
                        'ref_id': quality_point.id,
                        'routing_id': child.id,
                        'operation_id': child_operation[0].id,
                    })

        return True


    @api.multi
    def _sync_operation(self):
        """
        1. remove motherless operations (withnot new ref_id)
        2. udpate all chidren's operations
        3. create all missings operations by duplicate them
        :return: bool
        """
        for record in self:

            # remove motherless operations
            child_operation_to_delete = record.child_ids.mapped('operation_ids').filtered(lambda x: x.ref_id != -1 and x.ref_id not in record.operation_ids.ids)
            # _logger.warning('[SYNC] remove motherless operations: %r' % (child_operation_to_delete.ids))
            child_operation_to_delete.unlink()

            # update all children's operations
            for operation in record.operation_ids:
                to_update = record.child_ids.mapped('operation_ids').filtered(lambda x: x.ref_id == operation.id)
                # _logger.warning('[SYNC] update all child operations: %r' % (to_update.ids))
                to_update.update(operation._prepare_child_vals())

            # create (by copy) all missing operations from parent
            for child in record.child_ids:
                missing_operations = record.operation_ids.filtered(lambda x: x.id not in child.operation_ids.mapped('ref_id'))
                # _logger.warning('[SYNC] create missing operations: %r' % (missing_operations.ids))

                for operation in missing_operations:
                    new_operation = operation.copy({
                        'ref_id': operation.id,
                        'routing_id': child.id,
                    })

        return True




    

