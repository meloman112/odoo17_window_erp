# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    is_installation_task = fields.Boolean(
        string='Задача монтажа',
        default=False,
    )
    installer_team_id = fields.Many2one(
        'res.users',
        string='Бригада монтажников',
        tracking=True,
    )
    planned_date = fields.Datetime(
        string='Запланированная дата монтажа',
        tracking=True,
    )
    delivery_date = fields.Date(
        string='Дата доставки',
        tracking=True,
    )
    installation_photos = fields.Many2many(
        'ir.attachment',
        'window_installation_photo_rel',
        'task_id',
        'attachment_id',
        string='Фотографии монтажа',
        domain="[('res_model', '=', 'project.task')]",
    )
    installation_state = fields.Selection(
        [
            ('assigned', 'Назначено'),
            ('delivery', 'Доставка'),
            ('installation', 'Монтаж'),
            ('cleaning', 'Уборка'),
            ('act', 'Акт'),
        ],
        string='Статус монтажа',
        default='assigned',
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Заказ',
        ondelete='set null',
    )
    window_measure_id = fields.Many2one(
        'window.measure',
        string='Замер',
        related='sale_order_id.window_measure_id',
        store=True,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            if task.is_installation_task:
                task._set_installation_defaults()
        return tasks

    def write(self, vals):
        result = super().write(vals)
        if 'installation_state' in vals:
            for task in self:
                if task.is_installation_task:
                    task._update_installation_state()
        return result

    def _set_installation_defaults(self):
        """Установить значения по умолчанию для задачи монтажа"""
        if not self.planned_date:
            self.planned_date = fields.Datetime.now()

    def _update_installation_state(self):
        """Обновить статус при изменении состояния монтажа"""
        if self.installation_state == 'act' and self.sale_order_id:
            # Обновить статус лида
            if self.sale_order_id.opportunity_id:
                stage_completed = self.env['crm.stage'].search([
                    ('name', '=', 'Завершено')
                ], limit=1)
                if stage_completed:
                    self.sale_order_id.opportunity_id.stage_id = stage_completed.id
                self.sale_order_id.opportunity_id.installation_id = self.id

    def action_start_delivery(self):
        """Начать доставку"""
        self.write({'installation_state': 'delivery'})

    def action_start_installation(self):
        """Начать монтаж"""
        self.write({'installation_state': 'installation'})

    def action_start_cleaning(self):
        """Начать уборку"""
        self.write({'installation_state': 'cleaning'})

    def action_create_act(self):
        """Создать акт выполненных работ"""
        self.ensure_one()
        
        if not self.sale_order_id:
            raise UserError(_('Не указан заказ для создания акта.'))
        
        self.write({'installation_state': 'act'})
        
        return self.sale_order_id.action_print_act()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    is_installation_project = fields.Boolean(
        string='Проект монтажа',
        default=False,
    )

