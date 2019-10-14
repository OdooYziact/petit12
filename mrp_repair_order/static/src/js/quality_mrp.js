odoo.define('mrp_repair_order.update_kanban', function (require) {
"use strict";

var basic_fields = require('web.basic_fields');
var core = require('web.core');
var field_registry = require('web.field_registry');
var KanbanController = require('web.KanbanController');
var KanbanRecord = require('web.KanbanRecord');
var KanbanView = require('web.KanbanView');
var view_registry = require('web.view_registry');
var ControlPanel = require('web.ControlPanel');

var FieldInteger = basic_fields.FieldInteger;
var FieldBinaryImage = basic_fields.FieldBinaryImage;


var BackArrow2 = FieldInteger.extend({
    events: {
        'click': '_onClick',
    },
    _render: function () {
        this.$el.html('<button class="btn btn-default o_workorder_icon_btn o_workorder_icon_back"><i class="fa fa-arrow-left"/></button>');
    },
    _onClick: function() {
        var self = this;
        this._rpc({
            method: 'action_back',
            model: 'mrp.workorder',
            args: [self.recordData.id],
        }).then(function () {
            self.do_action('mrp_repair_order.mrp_workorder_action_tablet', {
                additional_context: {
                    active_id: self.record.data.workcenter_id.res_id,
                    production_id: self.record.data.production_id.res_id
                },
                checkReadArgs: true,
                clear_breadcrumbs: true,
                action_buttons : false,
            });

        });
    },
});

field_registry.add('back_arrow_2', BackArrow2);
});
