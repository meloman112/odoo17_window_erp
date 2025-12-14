# -*- coding: utf-8 -*-
{
    'name': 'Window CRM Extension',
    'version': '17.0.1.0.0',
    'category': 'Sales/Windows',
    'summary': 'Расширение CRM для оконного бизнеса',
    'description': """
        Расширение CRM для оконного бизнеса:
        - Дополнительные стейджи CRM
        - Дополнительные поля в лидах
        - Интеграция с замерами, заказами, производством, монтажом
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'window_measurement',
        'window_offer',
        'window_production',
        'window_installation',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/crm_stage_data.xml',
        'views/crm_lead_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

