# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    telegram_user_id = fields.Many2one('telegram.user', string='Telegram пользователь', ondelete='set null')
    telegram_message_ids = fields.One2many('telegram.message', 'crm_lead_id', string='Telegram сообщения')

    @api.onchange('partner_id')
    def _onchange_partner_id_telegram(self):
        """Автоматически заполнить Telegram пользователя из партнера"""
        if self.partner_id and self.partner_id.telegram_user_id:
            self.telegram_user_id = self.partner_id.telegram_user_id
        elif not self.partner_id:
            self.telegram_user_id = False

    def write(self, vals):
        """Отслеживать изменение стадии и отправлять уведомления"""
        result = super().write(vals)
        
        # Если изменилась стадия лида
        if 'stage_id' in vals:
            for lead in self:
                lead._send_stage_notification()
        
        return result

    def _send_stage_notification(self):
        """Отправить уведомление об изменении стадии лида"""
        self.ensure_one()
        
        # Найти Telegram пользователя
        telegram_user = self.telegram_user_id
        if not telegram_user or not telegram_user.is_verified:
            return
        
        if not self.stage_id:
            return
        
        message = (
            f"📋 **Изменение статуса лида**\n\n"
            f"Лид: {self.name}\n"
            f"Новая стадия: **{self.stage_id.name}**\n"
            f"Дата: {fields.Datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        if self.expected_revenue:
            message += f"\n\nОжидаемая выручка: {self.company_currency_id.symbol} {self.expected_revenue:.2f}"
        
        try:
            telegram_user._send_telegram_message(message)
            
            # Сохранить в истории сообщений и привязать к лиду
            self.env['telegram.message'].create({
                'telegram_user_id': telegram_user.id,
                'crm_lead_id': self.id,
                'message_date': fields.Datetime.now(),
                'text': message,
                'direction': 'outgoing',
            })
        except Exception as e:
            _logger.error(f"Ошибка отправки уведомления о стадии лида в Telegram: {str(e)}")

    def action_send_telegram_message(self):
        """Открыть форму отправки сообщения в Telegram"""
        self.ensure_one()
        if not self.telegram_user_id:
            raise UserError(_('Telegram пользователь не привязан к лиду'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Отправить сообщение в Telegram'),
            'res_model': 'telegram.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_telegram_user_id': self.telegram_user_id.id,
                'default_crm_lead_id': self.id,
            }
        }

