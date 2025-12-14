# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class WindowServiceTicket(models.Model):
    _name = 'window.service.ticket'
    _description = 'Window Service Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Номер обращения',
        required=True,
        default=lambda self: _('New'),
        copy=False,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Клиент',
        required=True,
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Заказ',
        ondelete='set null',
        domain="[('is_window_order', '=', True)]",
        tracking=True,
    )
    installation_task_id = fields.Many2one(
        'project.task',
        string='Задача монтажа',
        ondelete='set null',
        domain="[('is_installation_task', '=', True)]",
        tracking=True,
    )
    window_measure_id = fields.Many2one(
        'window.measure',
        string='Замер',
        related='sale_order_id.window_measure_id',
        store=True,
        readonly=True,
    )
    installation_date = fields.Date(
        string='Дата установки',
        tracking=True,
    )
    warranty_status = fields.Selection(
        [
            ('in_warranty', 'На гарантии'),
            ('out_of_warranty', 'Вне гарантии'),
            ('extended_warranty', 'Расширенная гарантия'),
        ],
        string='Статус гарантии',
        default='in_warranty',
        tracking=True,
        compute='_compute_warranty_status',
        store=True,
    )
    type_of_issue = fields.Selection(
        [
            ('seal', 'Уплотнитель'),
            ('hardware', 'Фурнитура'),
            ('glass', 'Стеклопакет'),
            ('profile', 'Профиль'),
            ('installation', 'Монтаж'),
            ('other', 'Другое'),
        ],
        string='Тип проблемы',
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string='Описание проблемы',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ('new', 'Новое'),
            ('assigned', 'Назначено'),
            ('in_progress', 'В работе'),
            ('resolved', 'Решено'),
            ('closed', 'Закрыто'),
        ],
        string='Статус',
        default='new',
        tracking=True,
    )
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Назначен на',
        tracking=True,
    )
    resolution = fields.Text(
        string='Решение',
        tracking=True,
    )
    date_resolved = fields.Datetime(
        string='Дата решения',
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('window.service.ticket') or _('New')
        tickets = super().create(vals_list)
        for ticket in tickets:
            if ticket.sale_order_id:
                ticket._update_warranty_status()
        return tickets

    def write(self, vals):
        result = super().write(vals)
        if 'sale_order_id' in vals or 'installation_date' in vals:
            for ticket in self:
                if ticket.sale_order_id:
                    ticket._update_warranty_status()
        if 'state' in vals and vals['state'] == 'resolved':
            for ticket in self:
                ticket.date_resolved = fields.Datetime.now()
        return result

    @api.depends('installation_date', 'sale_order_id', 'installation_task_id')
    def _compute_warranty_status(self):
        """Вычислить статус гарантии на основе даты установки"""
        for ticket in self:
            if not ticket.installation_date:
                # Попытаться получить дату из задачи монтажа или заказа
                if ticket.installation_task_id and ticket.installation_task_id.date_deadline:
                    ticket.installation_date = ticket.installation_task_id.date_deadline.date()
                elif ticket.sale_order_id and ticket.sale_order_id.date_order:
                    # Примерная дата установки через 21 день после заказа
                    if isinstance(ticket.sale_order_id.date_order, fields.Datetime):
                        ticket.installation_date = (ticket.sale_order_id.date_order.date() + timedelta(days=21))
                    else:
                        ticket.installation_date = (ticket.sale_order_id.date_order + timedelta(days=21))
            
            if ticket.installation_date:
                warranty_period = timedelta(days=365 * 5)  # 5 лет гарантии
                warranty_end_date = ticket.installation_date + warranty_period
                
                if fields.Date.today() <= warranty_end_date:
                    ticket.warranty_status = 'in_warranty'
                else:
                    ticket.warranty_status = 'out_of_warranty'
            else:
                ticket.warranty_status = 'in_warranty'  # По умолчанию на гарантии

    def _update_warranty_status(self):
        """Обновить статус гарантии"""
        self._compute_warranty_status()

    def action_assign(self):
        """Назначить обращение"""
        self.write({
            'state': 'assigned',
            'assigned_user_id': self.env.user.id,
        })

    def action_start(self):
        """Начать работу над обращением"""
        self.write({'state': 'in_progress'})

    def action_resolve(self):
        """Решить обращение"""
        if not self.resolution:
            raise UserError(_('Необходимо указать решение перед закрытием обращения.'))
        self.write({
            'state': 'resolved',
            'date_resolved': fields.Datetime.now(),
        })

    def action_close(self):
        """Закрыть обращение"""
        self.write({'state': 'closed'})

    def action_view_sale_order(self):
        """Открыть заказ"""
        self.ensure_one()
        if not self.sale_order_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Заказ'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
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

