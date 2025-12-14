# -*- coding: utf-8 -*-
{
    'name': 'Учебный центр',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Управление курсами, студентами и записями на курсы',
    'description': """
        Модуль для управления учебным центром:
        - Управление курсами
        - Управление студентами
        - Записи студентов на курсы
        - Отслеживание прогресса обучения
    """,
    'author': 'Education Center',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/course_views.xml',
        'views/student_views.xml',
        'views/enrollment_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

