# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Student(models.Model):
    """Модель студента"""
    _name = 'education.student'
    _description = 'Студент'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='ФИО', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Телефон', tracking=True)
    birth_date = fields.Date(string='Дата рождения', tracking=True)
    
    # Связь с партнером (опционально)
    partner_id = fields.Many2one('res.partner', string='Контакт', 
                                  help='Связь с контактом в системе')
    
    # Связи с курсами
    enrollment_ids = fields.One2many('education.enrollment', 'student_id', string='Записи на курсы')
    course_ids = fields.Many2many('education.course', 
                                  compute='_compute_course_ids', 
                                  string='Курсы')
    
    # Статистика
    enrollment_count = fields.Integer(string='Количество записей', compute='_compute_enrollment_count')
    completed_courses_count = fields.Integer(string='Завершенных курсов', compute='_compute_completed_courses_count')
    
    # Дополнительная информация
    notes = fields.Text(string='Заметки')
    active = fields.Boolean(string='Активен', default=True)
    
    @api.depends('enrollment_ids')
    def _compute_course_ids(self):
        """Вычисляет список курсов студента"""
        for student in self:
            student.course_ids = student.enrollment_ids.mapped('course_id')
    
    @api.depends('enrollment_ids')
    def _compute_enrollment_count(self):
        """Подсчитывает количество записей студента"""
        for student in self:
            student.enrollment_count = len(student.enrollment_ids)
    
    @api.depends('enrollment_ids', 'enrollment_ids.state')
    def _compute_completed_courses_count(self):
        """Подсчитывает количество завершенных курсов"""
        for student in self:
            student.completed_courses_count = len(student.enrollment_ids.filtered(
                lambda e: e.state == 'completed'
            ))
    
    def action_open_enrollments(self):
        """Открывает список записей студента"""
        self.ensure_one()
        return {
            'name': f'Записи студента: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'education.enrollment',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }
    
    def action_open_courses(self):
        """Открывает список курсов студента"""
        self.ensure_one()
        return {
            'name': f'Курсы студента: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'education.course',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.course_ids.ids)],
        }

