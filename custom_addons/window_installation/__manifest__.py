# -*- coding: utf-8 -*-
{
    'name': 'Window Installation',
    'version': '17.0.1.0.0',
    'category': 'Services/Windows',
    'summary': 'Управление монтажом окон',
    'description': """
        Модуль для управления монтажом окон:
        - Создание задач монтажа из заказов
        - Управление бригадами монтажников
        - Отслеживание статусов монтажа
        - Фотографии монтажа
        - Интеграция с проектами
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'sale',
        'stock',
        'window_offer',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/project_data.xml',
        'views/project_task_views.xml',
        'views/sale_order_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

