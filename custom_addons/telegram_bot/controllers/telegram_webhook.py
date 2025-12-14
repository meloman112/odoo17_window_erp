# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class TelegramWebhookController(http.Controller):

    @http.route('/telegram/webhook/<string:secret>', type='json', auth='public', methods=['POST'], csrf=False)
    def telegram_webhook(self, secret, **kwargs):
        """
        Обработка webhook от Telegram
        
        Telegram отправляет POST запрос с JSON данными о сообщении
        """
        try:
            # Проверить secret
            bot_config = request.env['telegram.bot.config'].sudo().search([
                ('webhook_secret', '=', secret),
                ('active', '=', True)
            ], limit=1)
            
            if not bot_config:
                _logger.warning(f"Неверный webhook secret: {secret}")
                return {'ok': False, 'error': 'Invalid secret'}

            # Получить данные из запроса
            data = request.jsonrequest
            
            # Обработать обновление
            if 'message' in data:
                self._process_message(bot_config, data['message'])
            elif 'callback_query' in data:
                self._process_callback_query(bot_config, data['callback_query'])
            
            return {'ok': True}
            
        except Exception as e:
            _logger.error(f"Ошибка обработки webhook: {str(e)}", exc_info=True)
            return {'ok': False, 'error': str(e)}

    def _process_message(self, bot_config, message_data):
        """Обработать входящее сообщение"""
        try:
            chat_id = message_data.get('chat', {}).get('id')
            user_data = message_data.get('from', {})
            telegram_id = user_data.get('id')
            text = message_data.get('text', '')
            message_id = message_data.get('message_id')
            message_date = message_data.get('date')
            
            if not telegram_id or not chat_id:
                return
            
            # Найти или создать Telegram пользователя
            telegram_user = request.env['telegram.user'].sudo().search([
                ('telegram_id', '=', telegram_id)
            ], limit=1)
            
            if not telegram_user:
                # Создать нового пользователя (пока не верифицирован)
                telegram_user = request.env['telegram.user'].sudo().create({
                    'telegram_id': telegram_id,
                    'username': user_data.get('username'),
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'chat_id': chat_id,
                })
                
                # Отправить приветственное сообщение с инструкцией
                self._send_message(
                    bot_config.bot_token,
                    chat_id,
                    (
                        "👋 Добро пожаловать!\n\n"
                        "Для идентификации введите ваш код верификации.\n"
                        "Если у вас нет кода, обратитесь к менеджеру.\n\n"
                        f"Ваш код верификации: **{telegram_user.verification_code}**\n\n"
                        "Введите этот код в системе Odoo для завершения идентификации."
                    )
                )
                return
            
            # Обновить chat_id если изменился
            if telegram_user.chat_id != chat_id:
                telegram_user.sudo().write({'chat_id': chat_id})
            
            # Обработать команды
            if text.startswith('/'):
                self._process_command(bot_config, telegram_user, text)
                return
            
            # Если пользователь не верифицирован, проверить код верификации
            if not telegram_user.is_verified:
                # Проверить, не является ли текст кодом верификации (6 цифр)
                if text.strip().isdigit() and len(text.strip()) == 6:
                    if text.strip() == telegram_user.verification_code:
                        # Верифицировать пользователя
                        telegram_user.sudo().write({
                            'is_verified': True,
                            'verified_date': fields.Datetime.now(),
                        })
                        self._send_message(
                            bot_config.bot_token,
                            chat_id,
                            (
                                f"✅ Вы успешно идентифицированы как {telegram_user.partner_id.name}.\n\n"
                                "Теперь вы будете получать уведомления об изменении статуса ваших заказов.\n\n"
                                "Доступные команды:\n"
                                "/orders - список ваших заказов\n"
                                "/help - помощь"
                            )
                        )
                        return
                    else:
                        self._send_message(
                            bot_config.bot_token,
                            chat_id,
                            "❌ Неверный код верификации. Попробуйте еще раз."
                        )
                        return
                else:
                    self._send_message(
                        bot_config.bot_token,
                        chat_id,
                        (
                            "⚠️ Вы еще не идентифицированы.\n\n"
                            f"Ваш код верификации: **{telegram_user.verification_code}**\n\n"
                            "Введите этот 6-значный код для завершения идентификации."
                        )
                    )
                    return
            
            # Сохранить сообщение в истории
            from datetime import datetime
            message_date_dt = datetime.fromtimestamp(message_date) if message_date else datetime.now()
            
            request.env['telegram.message'].sudo().create({
                'telegram_user_id': telegram_user.id,
                'message_id': message_id,
                'message_date': message_date_dt,
                'text': text,
                'direction': 'incoming',
            })
            
            # Уведомить операторов
            self._notify_operators(bot_config, telegram_user, text)
            
        except Exception as e:
            _logger.error(f"Ошибка обработки сообщения: {str(e)}", exc_info=True)

    def _process_command(self, bot_config, telegram_user, text):
        """Обработать команду бота"""
        command = text.split()[0].lower()
        chat_id = telegram_user.chat_id
        
        if command == '/start':
            if telegram_user.is_verified:
                message = (
                    f"✅ Вы идентифицированы как {telegram_user.partner_id.name}\n\n"
                    "Вы будете получать уведомления об изменении статуса ваших заказов.\n\n"
                    "Доступные команды:\n"
                    "/orders - список ваших заказов\n"
                    "/help - помощь"
                )
            else:
                message = (
                    "👋 Добро пожаловать!\n\n"
                    f"Ваш код верификации: **{telegram_user.verification_code}**\n\n"
                    "Введите этот код в системе Odoo для завершения идентификации."
                )
            self._send_message(bot_config.bot_token, chat_id, message)
            
        elif command == '/orders':
            if not telegram_user.is_verified:
                self._send_message(bot_config.bot_token, chat_id, "⚠️ Вы не идентифицированы.")
                return
            
            # Получить заказы клиента
            orders = request.env['sale.order'].sudo().search([
                ('partner_id', '=', telegram_user.partner_id.id),
                ('state', '!=', 'cancel')
            ], limit=10, order='date_order desc')
            
            if not orders:
                self._send_message(bot_config.bot_token, chat_id, "У вас пока нет заказов.")
                return
            
            message_parts = ["📦 Ваши заказы:\n"]
            for order in orders:
                state_names = {
                    'draft': 'Черновик',
                    'sent': 'Отправлено',
                    'sale': 'Подтверждено',
                    'cancel': 'Отменено',
                }
                state_name = state_names.get(order.state, order.state)
                message_parts.append(
                    f"• {order.name} - {state_name}\n"
                    f"  Сумма: {order.currency_id.symbol} {order.amount_total:.2f}"
                )
            
            self._send_message(bot_config.bot_token, chat_id, '\n'.join(message_parts))
            
        elif command == '/help':
            message = (
                "📚 Доступные команды:\n\n"
                "/start - начать работу\n"
                "/orders - список ваших заказов\n"
                "/help - эта справка\n\n"
                "Вы также можете написать сообщение оператору."
            )
            self._send_message(bot_config.bot_token, chat_id, message)

    def _process_callback_query(self, bot_config, callback_data):
        """Обработать callback query (нажатие на кнопку)"""
        # Можно добавить обработку кнопок в будущем
        pass

    def _notify_operators(self, bot_config, telegram_user, text):
        """Уведомить операторов о новом сообщении от клиента"""
        if not bot_config.operator_user_ids:
            return
        
        # Здесь можно добавить уведомление операторов через Odoo
        # Например, создать задачу или отправить email
        pass

    def _send_message(self, bot_token, chat_id, text, parse_mode='Markdown'):
        """Отправить сообщение в Telegram"""
        import requests
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': parse_mode,
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            _logger.error(f"Ошибка отправки сообщения в Telegram: {str(e)}")
            return None

