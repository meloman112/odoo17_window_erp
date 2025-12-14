# -*- coding: utf-8 -*-
{
    'name': 'Telegram Bot Integration',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': 'Интеграция с Telegram ботом для уведомлений и чата',
    'description': """
        Модуль для интеграции с Telegram ботом:
        - Идентификация клиентов через Telegram
        - Уведомления об изменении статуса заказа
        - Чат с оператором
        - История сообщений
    """,
    'author': 'Window ERP',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'mail',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/telegram_data.xml',
        'views/telegram_bot_config_views.xml',
        'views/telegram_user_views.xml',
        'views/telegram_message_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

