# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    telegram_user_ids = fields.One2many('telegram.user', 'partner_id', string='Telegram пользователи')
    telegram_user_id = fields.Many2one('telegram.user', string='Основной Telegram', compute='_compute_telegram_user', store=False)
    has_telegram = fields.Boolean(string='Есть Telegram', compute='_compute_has_telegram', store=False)

    def _compute_telegram_user(self):
        for record in self:
            record.telegram_user_id = record.telegram_user_ids.filtered(lambda u: u.is_verified)[:1]

    def _compute_has_telegram(self):
        for record in self:
            record.has_telegram = bool(record.telegram_user_ids.filtered(lambda u: u.is_verified))

    def action_view_telegram_users(self):
        """Открыть Telegram пользователей"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Telegram пользователи',
            'res_model': 'telegram.user',
            'domain': [('partner_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

