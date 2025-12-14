# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Метод _create_production_order уже определен в window_offer
    # Здесь можно добавить дополнительную логику если нужно

    def action_view_production(self):
        """Открыть производственный заказ"""
        self.ensure_one()
        if not self.production_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Внимание'),
                    'message': _('Производственный заказ не создан.'),
                    'type': 'warning',
                }
            }
        
        action = {
            'name': _('Производственный заказ'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
            'target': 'current',
        }
        return action

