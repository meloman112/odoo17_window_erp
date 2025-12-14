# -*- coding: utf-8 -*-
{
    'name': 'Window ERP Base',
    'version': '17.0.1.0.0',
    'category': 'Sales/Windows',
    'summary': 'Базовый модуль для оконной ERP системы',
    'description': """
        Базовый модуль для интеграции всех модулей оконной ERP системы.
        Устанавливает зависимости и настраивает базовую конфигурацию.
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
        'stock',
        'account',
    ],
    'data': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

