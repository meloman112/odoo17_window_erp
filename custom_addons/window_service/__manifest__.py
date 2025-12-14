# -*- coding: utf-8 -*-
{
    'name': 'Window Service & Warranty',
    'version': '17.0.1.0.0',
    'category': 'Services/Windows',
    'summary': 'Гарантия и сервисное обслуживание окон',
    'description': """
        Модуль для управления гарантией и сервисом:
        - Сервисные обращения для окон
        - Отслеживание гарантийных случаев
        - Типы проблем с окнами
        - Интеграция с установками
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'sale',
        'project',
        'window_installation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/window_service_ticket_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

