# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    object_type = fields.Selection(
        [
            ('apartment', 'Квартира'),
            ('house', 'Дом'),
            ('office', 'Офис'),
            ('commercial', 'Коммерческое помещение'),
            ('other', 'Другое'),
        ],
        string='Тип объекта',
        tracking=True,
    )
    area_type = fields.Selection(
        [
            ('new_building', 'Новостройка'),
            ('secondary', 'Вторичное жилье'),
            ('renovation', 'Ремонт'),
            ('replacement', 'Замена окон'),
        ],
        string='Тип площади',
        tracking=True,
    )
    budget = fields.Monetary(
        string='Бюджет',
        currency_field='company_currency_id',
        tracking=True,
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        string='Валюта',
        related='company_id.currency_id',
        readonly=True,
    )
    lead_temperature = fields.Selection(
        [
            ('hot', 'Горячий'),
            ('warm', 'Теплый'),
            ('cold', 'Холодный'),
        ],
        string='Температура лида',
        default='cold',
        tracking=True,
    )
    desired_date_measure = fields.Date(
        string='Желаемая дата замера',
        tracking=True,
    )
    measurement_id = fields.Many2one(
        'window.measure',
        string='Замер',
        readonly=True,
        copy=False,
    )
    contract_id = fields.Many2one(
        'sale.order',
        string='Договор',
        readonly=True,
        copy=False,
        domain="[('state', 'in', ['sale', 'done'])]",
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Производственный заказ',
        readonly=True,
        copy=False,
    )
    installation_id = fields.Many2one(
        'project.task',
        string='Монтаж',
        readonly=True,
        copy=False,
        domain="[('project_id.name', '=', 'Монтаж')]",
    )
    delivery_date = fields.Date(
        string='Дата доставки',
        tracking=True,
    )
    final_payment_status = fields.Selection(
        [
            ('unpaid', 'Не оплачено'),
            ('partial', 'Частично оплачено'),
            ('paid', 'Оплачено'),
        ],
        string='Статус оплаты',
        default='unpaid',
        tracking=True,
    )

    def action_create_measurement(self):
        """Создать замер из лида"""
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_('Необходимо указать контакт для создания замера.'))
        
        measure = self.env['window.measure'].create({
            'deal_id': self.id,
            'customer_id': self.partner_id.id,
            'address': self.street or '',
            'date_planned': self.desired_date_measure or fields.Datetime.now(),
            'measurer_id': self.user_id.id if self.user_id else self.env.user.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Замер'),
            'res_model': 'window.measure',
            'res_id': measure.id,
            'view_mode': 'form',
            'target': 'current',
        }

