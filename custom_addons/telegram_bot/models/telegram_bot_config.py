# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TelegramBotConfig(models.Model):
    _name = 'telegram.bot.config'
    _description = 'Конфигурация Telegram бота'
    _rec_name = 'bot_name'

    bot_name = fields.Char(string='Имя бота', required=True)
    bot_token = fields.Char(string='Bot Token', required=True, help='Токен бота от @BotFather')
    webhook_url = fields.Char(string='Webhook URL', compute='_compute_webhook_url', store=False)
    webhook_secret = fields.Char(string='Webhook Secret', help='Секретный ключ для проверки webhook (только для webhook режима)')
    use_webhook = fields.Boolean(string='Использовать Webhook', default=False, help='Если выключено, используется long polling (getUpdates)')
    last_update_id = fields.Integer(string='Последний Update ID', default=0, help='Для long polling режима')
    active = fields.Boolean(string='Активен', default=True)
    operator_user_ids = fields.Many2many(
        'res.users',
        'telegram_bot_operator_rel',
        'bot_id',
        'user_id',
        string='Операторы',
        help='Пользователи, которые могут отвечать на сообщения клиентов'
    )

    @api.depends('bot_token')
    def _compute_webhook_url(self):
        """Вычислить URL для webhook"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.bot_token and base_url:
                record.webhook_url = f"{base_url}/telegram/webhook/{record.webhook_secret}"
            else:
                record.webhook_url = False

    def action_set_webhook(self):
        """Установить webhook для бота"""
        self.ensure_one()
        if not self.bot_token:
            raise UserError(_('Укажите Bot Token'))
        if not self.webhook_secret:
            raise UserError(_('Укажите Webhook Secret'))

        import requests
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        webhook_url = f"{base_url}/telegram/webhook/{self.webhook_secret}"

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/setWebhook",
                json={'url': webhook_url},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            if result.get('ok'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Успешно'),
                        'message': _('Webhook установлен'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_('Ошибка установки webhook: %s') % result.get('description', 'Unknown error'))
        except requests.exceptions.RequestException as e:
            raise UserError(_('Ошибка подключения к Telegram API: %s') % str(e))

    def action_delete_webhook(self):
        """Удалить webhook"""
        self.ensure_one()
        if not self.bot_token:
            raise UserError(_('Укажите Bot Token'))

        import requests
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook",
                timeout=10
            )
            response.raise_for_status()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Успешно'),
                    'message': _('Webhook удален'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except requests.exceptions.RequestException as e:
            raise UserError(_('Ошибка подключения к Telegram API: %s') % str(e))

    def get_active_bot(self):
        """Получить активного бота"""
        return self.search([('active', '=', True)], limit=1)

    @api.model
    def process_updates(self):
        """Обработать обновления через getUpdates (long polling) - вызывается из cron"""
        bot_config = self.get_active_bot()
        if not bot_config or bot_config.use_webhook:
            return
        
        import requests
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Получить обновления
            response = requests.get(
                f"https://api.telegram.org/bot{bot_config.bot_token}/getUpdates",
                params={
                    'offset': bot_config.last_update_id + 1,
                    'timeout': 10,
                    'allowed_updates': ['message', 'callback_query']
                },
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get('ok'):
                _logger.error(f"Ошибка получения обновлений: {result.get('description')}")
                return
            
            updates = result.get('result', [])
            if not updates:
                return
            
            # Обработать каждое обновление
            from odoo.addons.telegram_bot.models.telegram_message_handler import TelegramMessageHandler
            
            max_update_id = bot_config.last_update_id
            for update in updates:
                update_id = update.get('update_id')
                max_update_id = max(max_update_id, update_id)
                
                try:
                    # Обработать сообщение
                    if 'message' in update:
                        TelegramMessageHandler.process_message(bot_config, update['message'], self.env)
                    elif 'callback_query' in update:
                        TelegramMessageHandler._process_callback_query(bot_config, update['callback_query'], self.env)
                except Exception as e:
                    _logger.error(f"Ошибка обработки обновления {update_id}: {str(e)}", exc_info=True)
            
            # Сохранить последний обработанный update_id
            bot_config.sudo().write({'last_update_id': max_update_id})
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"Ошибка подключения к Telegram API: {str(e)}")
        except Exception as e:
            _logger.error(f"Ошибка обработки обновлений: {str(e)}", exc_info=True)

    def action_process_updates(self):
        """Ручной запуск обработки обновлений (для тестирования)"""
        self.ensure_one()
        if self.use_webhook:
            raise UserError(_('Включен режим webhook. Для ручной проверки отключите webhook.'))
        
        self.env['telegram.bot.config'].process_updates()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Успешно'),
                'message': _('Обновления проверены'),
                'type': 'success',
                'sticky': False,
            }
        }

