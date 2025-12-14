# -*- coding: utf-8 -*-
{
    'name': 'Window Measurement',
    'version': '17.0.1.0.0',
    'category': 'Sales/Windows',
    'summary': 'Управление замерами окон',
    'description': """
        Модуль для управления замерами окон:
        - Создание замеров из CRM лидов
        - Интеграция с проектами для задач замерщиков
        - Автоматическое создание КП после замера
        - Фото и технические параметры окон
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'project',
        'sale',
        'contacts',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/project_data.xml',
        'views/window_measure_views.xml',
        'views/crm_lead_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

