# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        """Отслеживать изменение статуса и отправлять уведомления"""
        result = super().write(vals)
        
        # Если изменился статус заказа
        if 'state' in vals:
            for order in self:
                order._send_status_notification(vals['state'])
        
        return result

    def _send_status_notification(self, new_state):
        """Отправить уведомление об изменении статуса заказа"""
        self.ensure_one()
        
        # Найти Telegram пользователя клиента
        telegram_user = self.partner_id.telegram_user_id
        if not telegram_user or not telegram_user.is_verified:
            return
        
        # Маппинг статусов на русский язык
        state_names = {
            'draft': 'Черновик',
            'sent': 'Отправлено',
            'sale': 'Подтверждено',
            'cancel': 'Отменено',
        }
        
        state_name = state_names.get(new_state, new_state)
        
        message = (
            f"📦 **Изменение статуса заказа**\n\n"
            f"Заказ: {self.name}\n"
            f"Новый статус: **{state_name}**\n"
            f"Дата: {fields.Datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Сумма: {self.currency_id.symbol} {self.amount_total:.2f}"
        )
        
        try:
            telegram_user._send_telegram_message(message)
            
            # Сохранить в истории сообщений
            self.env['telegram.message'].create({
                'telegram_user_id': telegram_user.id,
                'message_date': fields.Datetime.now(),
                'text': message,
                'direction': 'outgoing',
            })
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Ошибка отправки уведомления в Telegram: {str(e)}")

    def action_view_telegram_users(self):
        """Открыть Telegram пользователей клиента"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Telegram клиента',
            'res_model': 'telegram.user',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

