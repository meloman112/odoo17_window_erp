# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Enrollment(models.Model):
    """Модель записи на курс"""
    _name = 'education.enrollment'
    _description = 'Запись на курс'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'enrollment_date desc'
    _rec_name = 'display_name'

    # Основные поля
    student_id = fields.Many2one('education.student', string='Студент', 
                                 required=True, ondelete='cascade', tracking=True)
    course_id = fields.Many2one('education.course', string='Курс', 
                                required=True, ondelete='cascade', tracking=True)
    
    # Даты
    enrollment_date = fields.Date(string='Дата записи', required=True, 
                                  default=fields.Date.today, tracking=True)
    start_date = fields.Date(string='Дата начала обучения', tracking=True)
    end_date = fields.Date(string='Дата окончания обучения', tracking=True)
    
    # Статус
    state = fields.Selection([
        ('draft', 'Черновик'),
        ('enrolled', 'Записан'),
        ('in_progress', 'Идет обучение'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен')
    ], string='Статус', default='draft', tracking=True, required=True)
    
    # Оценки и прогресс
    final_grade = fields.Float(string='Итоговая оценка', digits=(5, 2))
    progress = fields.Float(string='Прогресс (%)', default=0.0, tracking=True)
    certificate_issued = fields.Boolean(string='Сертификат выдан', default=False, tracking=True)
    certificate_date = fields.Date(string='Дата выдачи сертификата')
    
    # Дополнительная информация
    notes = fields.Text(string='Заметки')
    active = fields.Boolean(string='Активна', default=True)
    
    # Вычисляемое поле для отображения
    display_name = fields.Char(string='Название', compute='_compute_display_name', store=True)
    
    @api.depends('student_id', 'course_id')
    def _compute_display_name(self):
        """Формирует название записи"""
        for enrollment in self:
            if enrollment.student_id and enrollment.course_id:
                enrollment.display_name = f"{enrollment.student_id.name} - {enrollment.course_id.name}"
            else:
                enrollment.display_name = 'Новая запись'
    
    @api.constrains('student_id', 'course_id')
    def _check_duplicate_enrollment(self):
        """Проверяет дублирование записи"""
        for enrollment in self:
            if enrollment.state != 'cancelled':
                duplicate = self.search([
                    ('student_id', '=', enrollment.student_id.id),
                    ('course_id', '=', enrollment.course_id.id),
                    ('id', '!=', enrollment.id),
                    ('state', '!=', 'cancelled')
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        f'Студент {enrollment.student_id.name} уже записан на курс {enrollment.course_id.name}'
                    )
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Проверяет корректность дат"""
        for enrollment in self:
            if enrollment.start_date and enrollment.end_date:
                if enrollment.end_date < enrollment.start_date:
                    raise ValidationError('Дата окончания не может быть раньше даты начала')
    
    def action_confirm(self):
        """Подтверждает запись"""
        for enrollment in self:
            if enrollment.state == 'draft':
                enrollment.write({
                    'state': 'enrolled',
                    'enrollment_date': fields.Date.today()
                })
    
    def action_start(self):
        """Начинает обучение"""
        for enrollment in self:
            if enrollment.state == 'enrolled':
                enrollment.write({
                    'state': 'in_progress',
                    'start_date': enrollment.start_date or fields.Date.today()
                })
    
    def action_complete(self):
        """Завершает обучение"""
        for enrollment in self:
            if enrollment.state == 'in_progress':
                enrollment.write({
                    'state': 'completed',
                    'end_date': enrollment.end_date or fields.Date.today(),
                    'progress': 100.0
                })
    
    def action_cancel(self):
        """Отменяет запись"""
        for enrollment in self:
            enrollment.write({'state': 'cancelled'})
    
    def action_issue_certificate(self):
        """Выдает сертификат"""
        for enrollment in self:
            if enrollment.state == 'completed' and not enrollment.certificate_issued:
                enrollment.write({
                    'certificate_issued': True,
                    'certificate_date': fields.Date.today()
                })

