# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import fields, api

_logger = logging.getLogger(__name__)


class TelegramMessageHandler:
    """Класс для обработки сообщений Telegram (используется и в webhook, и в long polling)"""
    
    @staticmethod
    def process_message(bot_config, message_data, env):
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
            telegram_user = env['telegram.user'].sudo().search([
                ('telegram_id', '=', telegram_id)
            ], limit=1)
            
            if not telegram_user:
                # Создать нового пользователя (пока не верифицирован)
                telegram_user = env['telegram.user'].sudo().create({
                    'telegram_id': telegram_id,
                    'username': user_data.get('username'),
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'chat_id': chat_id,
                })
                
                # Отправить приветственное сообщение с инструкцией
                TelegramMessageHandler._send_message(
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
                TelegramMessageHandler._process_command(bot_config, telegram_user, text, env)
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
                        # Перечитать запись для получения актуальных данных
                        telegram_user = env['telegram.user'].sudo().browse(telegram_user.id)
                        TelegramMessageHandler._send_message(
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
                        TelegramMessageHandler._send_message(
                            bot_config.bot_token,
                            chat_id,
                            "❌ Неверный код верификации. Попробуйте еще раз."
                        )
                        return
                else:
                    TelegramMessageHandler._send_message(
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
            message_date_dt = datetime.fromtimestamp(message_date) if message_date else datetime.now()
            
            # Найти лид по партнеру (берем первый активный лид)
            crm_lead_id = False
            if telegram_user.partner_id:
                lead = env['crm.lead'].sudo().search([
                    ('partner_id', '=', telegram_user.partner_id.id),
                    ('active', '=', True),
                ], order='create_date desc', limit=1)
                if lead:
                    crm_lead_id = lead.id
                    # Если у лида еще не привязан Telegram пользователь, привязать
                    if not lead.telegram_user_id:
                        lead.sudo().write({'telegram_user_id': telegram_user.id})
            
            env['telegram.message'].sudo().create({
                'telegram_user_id': telegram_user.id,
                'crm_lead_id': crm_lead_id,
                'message_id': message_id,
                'message_date': message_date_dt,
                'text': text,
                'direction': 'incoming',
            })
            
            # Уведомить операторов
            TelegramMessageHandler._notify_operators(bot_config, telegram_user, text, env)
            
        except Exception as e:
            _logger.error(f"Ошибка обработки сообщения: {str(e)}", exc_info=True)

    @staticmethod
    def _process_command(bot_config, telegram_user, text, env):
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
            TelegramMessageHandler._send_message(bot_config.bot_token, chat_id, message)
            
        elif command == '/orders':
            if not telegram_user.is_verified:
                TelegramMessageHandler._send_message(bot_config.bot_token, chat_id, "⚠️ Вы не идентифицированы.")
                return
            
            # Получить заказы клиента
            orders = env['sale.order'].sudo().search([
                ('partner_id', '=', telegram_user.partner_id.id),
                ('state', '!=', 'cancel')
            ], limit=10, order='date_order desc')
            
            if not orders:
                TelegramMessageHandler._send_message(bot_config.bot_token, chat_id, "У вас пока нет заказов.")
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
            
            TelegramMessageHandler._send_message(bot_config.bot_token, chat_id, '\n'.join(message_parts))
            
        elif command == '/help':
            message = (
                "📚 Доступные команды:\n\n"
                "/start - начать работу\n"
                "/orders - список ваших заказов\n"
                "/help - эта справка\n\n"
                "Вы также можете написать сообщение оператору."
            )
            TelegramMessageHandler._send_message(bot_config.bot_token, chat_id, message)

    @staticmethod
    def _process_callback_query(bot_config, callback_data, env):
        """Обработать callback query (нажатие на кнопку)"""
        # Можно добавить обработку кнопок в будущем
        pass

    @staticmethod
    def _notify_operators(bot_config, telegram_user, text, env):
        """Уведомить операторов о новом сообщении от клиента"""
        if not bot_config.operator_user_ids:
            return
        
        # Здесь можно добавить уведомление операторов через Odoo
        # Например, создать задачу или отправить email
        pass

    @staticmethod
    def _send_message(bot_token, chat_id, text, parse_mode='Markdown'):
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

