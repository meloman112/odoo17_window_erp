# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    window_order_id = fields.Many2one(
        'sale.order',
        string='Заказ на окна',
        ondelete='set null',
        readonly=True,
    )
    window_measure_id = fields.Many2one(
        'window.measure',
        string='Замер',
        related='window_order_id.window_measure_id',
        store=True,
        readonly=True,
    )

    def button_mark_done(self):
        """При завершении производства обновить статус заказа"""
        result = super().button_mark_done()
        
        for production in self:
            if production.window_order_id and production.window_order_id.is_window_order:
                # Обновить статус лида
                if production.window_order_id.opportunity_id:
                    # Переместить на стадию "Готово к доставке"
                    stage_ready = self.env['crm.stage'].search([
                        ('name', '=', 'Готово к доставке')
                    ], limit=1)
                    if stage_ready:
                        production.window_order_id.opportunity_id.stage_id = stage_ready.id
        
        return result

