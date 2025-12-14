# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_create_installation_task(self):
        """Создать задачу монтажа из заказа"""
        self.ensure_one()
        
        if not self.is_window_order:
            raise UserError(_('Это не заказ на окна.'))
        
        if self.installation_task_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Задача монтажа'),
                'res_model': 'project.task',
                'res_id': self.installation_task_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Найти проект "Монтаж"
        project = self.env['project.project'].search([
            ('name', '=', 'Монтаж'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not project:
            raise UserError(_('Проект "Монтаж" не найден. Создайте его вручную или установите данные модуля.'))
        
        # Создать задачу
        task = self.env['project.task'].create({
            'name': f'Монтаж: {self.name} - {self.partner_id.name}',
            'project_id': project.id,
            'is_installation_task': True,
            'sale_order_id': self.id,
            'planned_date': self.installation_planned_date or fields.Datetime.now(),
            'delivery_date': self.installation_delivery_date,
            'user_ids': [],  # Назначится позже
            'description': f"""
Заказ: {self.name}
Клиент: {self.partner_id.name}
Адрес: {self.partner_id.street or ''}
            """.strip(),
        })
        
        self.installation_task_id = task.id
        
        # Обновить лид
        if self.opportunity_id:
            self.opportunity_id.installation_id = task.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Задача монтажа'),
            'res_model': 'project.task',
            'res_id': task.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_installation_task(self):
        """Открыть задачу монтажа"""
        self.ensure_one()
        if not self.installation_task_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Задача монтажа'),
            'res_model': 'project.task',
            'res_id': self.installation_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

