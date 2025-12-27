# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TelegramMessage(models.Model):
    _name = 'telegram.message'
    _description = 'Сообщение Telegram'
    _order = 'message_date desc, id desc'

    telegram_user_id = fields.Many2one('telegram.user', string='Telegram пользователь', required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner', string='Клиент', related='telegram_user_id.partner_id', store=True, index=True)
    crm_lead_id = fields.Many2one('crm.lead', string='Лид', ondelete='cascade', index=True, help='Лид, к которому относится сообщение')
    message_id = fields.Integer(string='Message ID', help='ID сообщения в Telegram')
    message_date = fields.Datetime(string='Дата сообщения', required=True, index=True)
    text = fields.Text(string='Текст сообщения')
    direction = fields.Selection([
        ('incoming', 'Входящее'),
        ('outgoing', 'Исходящее'),
    ], string='Направление', required=True, default='incoming')
    user_id = fields.Many2one('res.users', string='Оператор', help='Оператор, который отправил ответ')
    is_read = fields.Boolean(string='Прочитано', default=False)
    reply_to_message_id = fields.Many2one('telegram.message', string='Ответ на сообщение')

    def action_send_reply(self):
        """Отправить ответ клиенту"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Отправить ответ'),
            'res_model': 'telegram.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_telegram_user_id': self.telegram_user_id.id,
                'default_reply_to_message_id': self.id,
            }
        }


class TelegramMessageWizard(models.TransientModel):
    _name = 'telegram.message.wizard'
    _description = 'Мастер отправки сообщения в Telegram'

    telegram_user_id = fields.Many2one('telegram.user', string='Telegram пользователь', required=True)
    crm_lead_id = fields.Many2one('crm.lead', string='Лид')
    reply_to_message_id = fields.Many2one('telegram.message', string='Ответ на сообщение')
    text = fields.Text(string='Текст сообщения', required=True)

    def action_send(self):
        """Отправить сообщение"""
        self.ensure_one()
        if not self.text:
            raise UserError(_('Введите текст сообщения'))
        
        # Отправить через Telegram API
        self.telegram_user_id._send_telegram_message(self.text)
        
        # Сохранить в истории
        self.env['telegram.message'].create({
            'telegram_user_id': self.telegram_user_id.id,
            'crm_lead_id': self.crm_lead_id.id if self.crm_lead_id else False,
            'message_date': fields.Datetime.now(),
            'text': self.text,
            'direction': 'outgoing',
            'user_id': self.env.user.id,
            'reply_to_message_id': self.reply_to_message_id.id if self.reply_to_message_id else False,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Успешно'),
                'message': _('Сообщение отправлено'),
                'type': 'success',
                'sticky': False,
            }
        }

