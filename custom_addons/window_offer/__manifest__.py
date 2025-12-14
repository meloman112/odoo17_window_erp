# -*- coding: utf-8 -*-
{
    'name': 'Window Offer & Contract',
    'version': '17.0.1.0.0',
    'category': 'Sales/Windows',
    'summary': 'Коммерческие предложения и договоры для окон',
    'description': """
        Модуль для управления коммерческими предложениями и договорами:
        - Генерация КП из замеров
        - Расчет стоимости окон
        - Создание договоров
        - PDF шаблоны для КП, договоров, спецификаций, актов
        - Интеграция с sale.order
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'sale_management',
        'account',
        'window_measurement',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sale_order_data.xml',
        'views/sale_order_views.xml',
        'report/report_templates.xml',
        'report/report_offer.xml',
        'report/report_contract.xml',
        'report/report_specification.xml',
        'report/report_act.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

