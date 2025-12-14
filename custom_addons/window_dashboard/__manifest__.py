# -*- coding: utf-8 -*-
{
    'name': 'Window Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Sales/Windows',
    'summary': 'Дашборды и KPI для оконного бизнеса',
    'description': """
        Модуль дашбордов и аналитики:
        - Воронка продаж
        - Производственный план
        - KPI замерщиков
        - KPI монтажников
        - Срок обработки лида
        - Доходность заказов
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'sale',
        'project',
        'mrp',
        'window_measurement',
        'window_offer',
        'window_production',
        'window_installation',
        'window_service',
    ],
    'data': [
        'views/dashboard_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

