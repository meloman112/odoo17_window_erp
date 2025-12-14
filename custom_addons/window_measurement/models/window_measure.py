# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class WindowMeasure(models.Model):
    _name = 'window.measure'
    _description = 'Window Measurement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_planned desc, id desc'

    name = fields.Char(
        string='Номер замера',
        required=True,
        default=lambda self: _('New'),
        copy=False,
        tracking=True,
    )
    deal_id = fields.Many2one(
        'crm.lead',
        string='Сделка',
        required=True,
        ondelete='cascade',
        tracking=True,
        domain="[('type', '=', 'opportunity')]",
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Клиент',
        related='deal_id.partner_id',
        store=True,
        readonly=True,
    )
    address = fields.Text(
        string='Адрес замера',
        required=True,
        tracking=True,
    )
    date_planned = fields.Datetime(
        string='Запланированная дата',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    date_done = fields.Datetime(
        string='Дата выполнения',
        tracking=True,
    )
    measurer_id = fields.Many2one(
        'res.users',
        string='Замерщик',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    photos = fields.Many2many(
        'ir.attachment',
        'window_measure_photo_rel',
        'measure_id',
        'attachment_id',
        string='Фотографии',
        domain="[('res_model', '=', 'window.measure')]",
    )
    room_type = fields.Selection(
        [
            ('living_room', 'Гостиная'),
            ('bedroom', 'Спальня'),
            ('kitchen', 'Кухня'),
            ('bathroom', 'Ванная'),
            ('balcony', 'Балкон'),
            ('office', 'Офис'),
            ('other', 'Другое'),
        ],
        string='Тип помещения',
        tracking=True,
    )
    profile_type = fields.Selection(
        [
            ('pvc_3', 'ПВХ 3-камерный'),
            ('pvc_5', 'ПВХ 5-камерный'),
            ('pvc_7', 'ПВХ 7-камерный'),
            ('aluminum', 'Алюминий'),
            ('wood', 'Дерево'),
            ('wood_aluminum', 'Дерево-алюминий'),
        ],
        string='Тип профиля',
        tracking=True,
    )
    glass_unit_type = fields.Selection(
        [
            ('single', 'Однокамерный'),
            ('double', 'Двухкамерный'),
            ('triple', 'Трехкамерный'),
            ('energy_saving', 'Энергосберегающий'),
            ('soundproof', 'Шумоизоляционный'),
        ],
        string='Тип стеклопакета',
        tracking=True,
    )
    color = fields.Char(
        string='Цвет',
        tracking=True,
    )
    width = fields.Float(
        string='Ширина (мм)',
        digits=(16, 1),
        tracking=True,
    )
    height = fields.Float(
        string='Высота (мм)',
        digits=(16, 1),
        tracking=True,
    )
    installation_complexity = fields.Selection(
        [
            ('simple', 'Простой'),
            ('medium', 'Средний'),
            ('complex', 'Сложный'),
            ('very_complex', 'Очень сложный'),
        ],
        string='Сложность монтажа',
        tracking=True,
    )
    comments = fields.Text(
        string='Комментарии',
        tracking=True,
    )
    task_id = fields.Many2one(
        'project.task',
        string='Задача в проекте',
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        [
            ('draft', 'Черновик'),
            ('planned', 'Запланирован'),
            ('in_progress', 'В работе'),
            ('done', 'Выполнен'),
            ('cancelled', 'Отменен'),
        ],
        string='Статус',
        default='draft',
        tracking=True,
    )
    offer_id = fields.Many2one(
        'sale.order',
        string='Коммерческое предложение',
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('window.measure') or _('New')
        measures = super().create(vals_list)
        for measure in measures:
            measure._create_task()
        return measures

    def write(self, vals):
        result = super().write(vals)
        if 'state' in vals or 'measurer_id' in vals:
            for measure in self:
                if measure.task_id:
                    measure._update_task()
        return result

    def _create_task(self):
        """Создать задачу в проекте 'Замеры'"""
        company_id = self.company_id.id if hasattr(self, 'company_id') and self.company_id else self.env.company.id
        project = self.env['project.project'].search([
            ('name', '=', 'Замеры'),
            ('company_id', '=', company_id)
        ], limit=1)
        
        if not project:
            raise UserError(_('Проект "Замеры" не найден. Создайте его вручную или установите данные модуля.'))

        task = self.env['project.task'].create({
            'name': f'Замер: {self.name} - {self.customer_id.name or self.deal_id.name}',
            'project_id': project.id,
            'user_ids': [(6, 0, [self.measurer_id.id])] if self.measurer_id else [],
            'date_deadline': self.date_planned,
            'description': f"""
Адрес: {self.address}
Клиент: {self.customer_id.name or self.deal_id.name}
Сделка: {self.deal_id.name}
            """.strip(),
            'window_measure_id': self.id,
        })
        self.task_id = task.id
        return task

    def _update_task(self):
        """Обновить задачу при изменении статуса или замерщика"""
        if not self.task_id:
            return
        
        self.task_id.write({
            'user_ids': [(6, 0, [self.measurer_id.id])] if self.measurer_id else [],
            'date_deadline': self.date_planned,
        })
        
        if self.state == 'done':
            self.task_id.write({'stage_id': self.env.ref('project.project_stage_2').id})
        elif self.state == 'cancelled':
            self.task_id.write({'stage_id': self.env.ref('project.project_stage_3').id})

    def action_confirm(self):
        """Подтвердить замер"""
        self.write({
            'state': 'planned',
            'date_planned': self.date_planned or fields.Datetime.now(),
        })

    def action_start(self):
        """Начать замер"""
        self.write({'state': 'in_progress'})

    def action_done(self):
        """Завершить замер"""
        if not self.width or not self.height:
            raise ValidationError(_('Необходимо указать ширину и высоту окна.'))
        
        self.write({
            'state': 'done',
            'date_done': fields.Datetime.now(),
        })
        
        # Обновить статус сделки
        if self.deal_id:
            stage_measure_done = self.env['crm.stage'].search([
                ('name', '=', 'Замер выполнен')
            ], limit=1)
            if stage_measure_done:
                self.deal_id.stage_id = stage_measure_done.id
            self.deal_id.measurement_id = self.id

    def action_create_offer(self):
        """Создать коммерческое предложение"""
        self.ensure_one()
        
        if not self.customer_id:
            raise UserError(_('Не указан клиент для создания КП.'))
        
        if self.offer_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Коммерческое предложение'),
                'res_model': 'sale.order',
                'res_id': self.offer_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Проверить наличие поля window_measure_id в модели sale.order
        sale_order_model = self.env['sale.order']
        order_vals = {
            'partner_id': self.customer_id.id,
            'opportunity_id': self.deal_id.id if self.deal_id else False,
            'date_order': fields.Datetime.now(),
        }
        
        # Добавить поле window_measure_id только если оно существует
        if 'window_measure_id' in sale_order_model._fields:
            order_vals['window_measure_id'] = self.id
        
        # Создать заказ
        order = self.env['sale.order'].create(order_vals)
        
        self.offer_id = order.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Коммерческое предложение'),
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        """Отменить замер"""
        self.write({'state': 'cancelled'})
        if self.task_id:
            self.task_id.write({'active': False})

    def action_view_task(self):
        """Открыть задачу проекта"""
        self.ensure_one()
        if not self.task_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Задача'),
            'res_model': 'project.task',
            'res_id': self.task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """Поиск по номеру, клиенту или адресу"""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|',
                     ('name', operator, name),
                     ('customer_id.name', operator, name),
                     ('address', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    window_measure_id = fields.Many2one(
        'window.measure',
        string='Замер',
        ondelete='set null',
    )

