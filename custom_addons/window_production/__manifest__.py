# -*- coding: utf-8 -*-
{
    'name': 'Window Production',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing/Windows',
    'summary': 'Производство окон - интеграция с MRP',
    'description': """
        Модуль для управления производством окон:
        - Автоматическое создание производственных заказов
        - Динамическое создание BOM
        - Интеграция с sale.order
        - Отслеживание статусов производства
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mrp',
        'sale',
        'stock',
        'window_offer',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        'views/sale_order_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

