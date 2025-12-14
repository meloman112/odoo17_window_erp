# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Course(models.Model):
    """Модель курса"""
    _name = 'education.course'
    _description = 'Курс'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Название курса', required=True, tracking=True)
    code = fields.Char(string='Код курса', required=True, copy=False, tracking=True)
    description = fields.Html(string='Описание курса')
    duration_hours = fields.Float(string='Длительность (часы)', required=True, tracking=True)
    price = fields.Monetary(string='Стоимость', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Валюта', 
                                   default=lambda self: self.env.company.currency_id)
    
    # Связи
    instructor_id = fields.Many2one('res.users', string='Преподаватель', 
                                     domain=[('share', '=', False)], tracking=True)
    enrollment_ids = fields.One2many('education.enrollment', 'course_id', string='Записи на курс')
    student_ids = fields.Many2many('education.student', 
                                    compute='_compute_student_ids', 
                                    string='Студенты')
    
    # Статистика
    enrollment_count = fields.Integer(string='Количество записей', compute='_compute_enrollment_count')
    active_student_count = fields.Integer(string='Активных студентов', compute='_compute_active_student_count')
    
    # Статус
    state = fields.Selection([
        ('draft', 'Черновик'),
        ('open', 'Открыт для записи'),
        ('in_progress', 'Идет обучение'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен')
    ], string='Статус', default='draft', tracking=True, required=True)
    
    active = fields.Boolean(string='Активен', default=True)
    
    @api.depends('enrollment_ids')
    def _compute_student_ids(self):
        """Вычисляет список студентов курса"""
        for course in self:
            course.student_ids = course.enrollment_ids.mapped('student_id')
    
    @api.depends('enrollment_ids')
    def _compute_enrollment_count(self):
        """Подсчитывает количество записей на курс"""
        for course in self:
            course.enrollment_count = len(course.enrollment_ids)
    
    @api.depends('enrollment_ids', 'enrollment_ids.state')
    def _compute_active_student_count(self):
        """Подсчитывает количество активных студентов"""
        for course in self:
            course.active_student_count = len(course.enrollment_ids.filtered(
                lambda e: e.state in ['enrolled', 'in_progress']
            ))
    
    def action_open_enrollments(self):
        """Открывает список записей на курс"""
        self.ensure_one()
        return {
            'name': f'Записи на курс: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'education.enrollment',
            'view_mode': 'tree,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
        }
    
    def action_open_students(self):
        """Открывает список студентов курса"""
        self.ensure_one()
        return {
            'name': f'Студенты курса: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'education.student',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.student_ids.ids)],
        }

