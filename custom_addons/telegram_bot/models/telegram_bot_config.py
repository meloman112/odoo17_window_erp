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
    webhook_secret = fields.Char(string='Webhook Secret', required=True, help='Секретный ключ для проверки webhook')
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

