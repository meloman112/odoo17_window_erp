# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class TelegramUser(models.Model):
    _name = 'telegram.user'
    _description = 'Telegram пользователь'
    _rec_name = 'display_name'

    telegram_id = fields.Integer(string='Telegram ID', required=True, index=True, help='ID пользователя в Telegram')
    username = fields.Char(string='Username', help='@username в Telegram')
    first_name = fields.Char(string='Имя')
    last_name = fields.Char(string='Фамилия')
    display_name = fields.Char(string='Отображаемое имя', compute='_compute_display_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Клиент', required=True, ondelete='cascade', index=True)
    verification_code = fields.Char(string='Код верификации', size=6, help='Код для идентификации клиента')
    is_verified = fields.Boolean(string='Верифицирован', default=False, index=True)
    verified_date = fields.Datetime(string='Дата верификации')
    chat_id = fields.Integer(string='Chat ID', help='ID чата для отправки сообщений')
    last_message_date = fields.Datetime(string='Последнее сообщение')
    message_count = fields.Integer(string='Количество сообщений', compute='_compute_message_count', store=False)

    _sql_constraints = [
        ('telegram_id_unique', 'unique(telegram_id)', 'Telegram ID должен быть уникальным'),
    ]

    @api.depends('first_name', 'last_name', 'username', 'telegram_id')
    def _compute_display_name(self):
        for record in self:
            name_parts = []
            if record.first_name:
                name_parts.append(record.first_name)
            if record.last_name:
                name_parts.append(record.last_name)
            if not name_parts and record.username:
                name_parts.append(f"@{record.username}")
            if not name_parts:
                name_parts.append(f"ID: {record.telegram_id}")
            record.display_name = ' '.join(name_parts)

    def _compute_message_count(self):
        for record in self:
            record.message_count = self.env['telegram.message'].search_count([
                ('telegram_user_id', '=', record.id)
            ])

    @api.model
    def create(self, vals):
        """Создать пользователя и сгенерировать код верификации"""
        # Если partner_id не указан, создать нового партнера
        if 'partner_id' not in vals or not vals.get('partner_id'):
            # Сформировать имя партнера
            name_parts = []
            if vals.get('first_name'):
                name_parts.append(vals['first_name'])
            if vals.get('last_name'):
                name_parts.append(vals['last_name'])
            if not name_parts and vals.get('username'):
                name_parts.append(f"@{vals['username']}")
            if not name_parts:
                name_parts.append(f"Telegram User {vals.get('telegram_id', '')}")
            
            partner_name = ' '.join(name_parts)
            
            # Создать партнера
            partner = self.env['res.partner'].sudo().create({
                'name': partner_name,
                'is_company': False,
            })
            vals['partner_id'] = partner.id
        
        # Сгенерировать код верификации если не указан
        if 'verification_code' not in vals or not vals.get('verification_code'):
            import random
            vals['verification_code'] = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        return super().create(vals)

    def action_verify(self):
        """Верифицировать пользователя"""
        self.ensure_one()
        if self.is_verified:
            raise UserError(_('Пользователь уже верифицирован'))
        
        self.write({
            'is_verified': True,
            'verified_date': fields.Datetime.now(),
        })
        
        # Отправить сообщение в Telegram
        self._send_telegram_message(
            f"✅ Вы успешно идентифицированы как {self.partner_id.name}.\n"
            f"Теперь вы будете получать уведомления об изменении статуса ваших заказов."
        )

    def action_send_verification_code(self):
        """Отправить код верификации в Telegram"""
        self.ensure_one()
        if not self.chat_id:
            raise UserError(_('Chat ID не установлен'))
        
        message = (
            f"🔐 Код верификации для идентификации:\n\n"
            f"**{self.verification_code}**\n\n"
            f"Введите этот код в системе Odoo для завершения идентификации."
        )
        
        self._send_telegram_message(message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Успешно'),
                'message': _('Код верификации отправлен в Telegram'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _send_telegram_message(self, text, parse_mode='Markdown'):
        """Отправить сообщение в Telegram"""
        bot_config = self.env['telegram.bot.config'].get_active_bot()
        if not bot_config:
            raise UserError(_('Активный бот не найден'))
        
        if not self.chat_id:
            raise UserError(_('Chat ID не установлен'))
        
        import requests
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_config.bot_token}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': parse_mode,
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise UserError(_('Ошибка отправки сообщения: %s') % str(e))

    def action_view_messages(self):
        """Открыть историю сообщений"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Сообщения'),
            'res_model': 'telegram.message',
            'domain': [('telegram_user_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

