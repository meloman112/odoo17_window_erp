# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    window_measure_id = fields.Many2one(
        'window.measure',
        string='Замер',
        ondelete='set null',
        tracking=True,
    )
    is_window_order = fields.Boolean(
        string='Заказ на окна',
        default=False,
        tracking=True,
    )
    # Технические параметры окон
    window_profile_type = fields.Selection(
        [
            ('pvc_3', 'ПВХ 3-камерный'),
            ('pvc_5', 'ПВХ 5-камерный'),
            ('pvc_7', 'ПВХ 7-камерный'),
            ('aluminum', 'Алюминий'),
            ('wood', 'Дерево'),
            ('wood_aluminum', 'Дерево-алюминий'),
        ],
        string='Тип профиля',
        tracking=True,
    )
    window_glass_unit_type = fields.Selection(
        [
            ('single', 'Однокамерный'),
            ('double', 'Двухкамерный'),
            ('triple', 'Трехкамерный'),
            ('energy_saving', 'Энергосберегающий'),
            ('soundproof', 'Шумоизоляционный'),
        ],
        string='Тип стеклопакета',
        tracking=True,
    )
    window_color = fields.Char(
        string='Цвет окон',
        tracking=True,
    )
    window_width = fields.Float(
        string='Ширина (мм)',
        digits=(16, 1),
        tracking=True,
    )
    window_height = fields.Float(
        string='Высота (мм)',
        digits=(16, 1),
        tracking=True,
    )
    installation_complexity = fields.Selection(
        [
            ('simple', 'Простой'),
            ('medium', 'Средний'),
            ('complex', 'Сложный'),
            ('very_complex', 'Очень сложный'),
        ],
        string='Сложность монтажа',
        tracking=True,
    )
    # Производство
    production_id = fields.Many2one(
        'mrp.production',
        string='Производственный заказ',
        readonly=True,
        copy=False,
    )
    production_state = fields.Selection(
        related='production_id.state',
        string='Статус производства',
        readonly=True,
    )
    # Монтаж
    installation_task_id = fields.Many2one(
        'project.task',
        string='Задача монтажа',
        readonly=True,
        copy=False,
        domain="[('project_id.name', '=', 'Монтаж')]",
    )
    installation_planned_date = fields.Datetime(
        string='Запланированная дата монтажа',
        tracking=True,
    )
    installation_delivery_date = fields.Date(
        string='Дата доставки',
        tracking=True,
    )
    # Документы
    offer_pdf = fields.Binary(
        string='КП PDF',
        attachment=True,
    )
    offer_pdf_name = fields.Char(
        string='Имя файла КП',
        default='kommercheskoe_predlozhenie.pdf',
    )
    contract_pdf = fields.Binary(
        string='Договор PDF',
        attachment=True,
    )
    contract_pdf_name = fields.Char(
        string='Имя файла договора',
        default='dogovor.pdf',
    )
    act_pdf = fields.Binary(
        string='Акт PDF',
        attachment=True,
    )
    act_pdf_name = fields.Char(
        string='Имя файла акта',
        default='akt_vypolnennyh_rabot.pdf',
    )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.window_measure_id:
                order._fill_from_measurement()
        return orders

    def write(self, vals):
        result = super().write(vals)
        if 'window_measure_id' in vals:
            for order in self:
                if order.window_measure_id:
                    order._fill_from_measurement()
        return result

    def _fill_from_measurement(self):
        """Заполнить данные из замера"""
        if not self.window_measure_id:
            return
        
        measure = self.window_measure_id
        self.write({
            'is_window_order': True,
            'window_profile_type': measure.profile_type,
            'window_glass_unit_type': measure.glass_unit_type,
            'window_color': measure.color,
            'window_width': measure.width,
            'window_height': measure.height,
            'installation_complexity': measure.installation_complexity,
        })

    def _action_confirm(self):
        """Подтвердить заказ и создать производственный заказ"""
        result = super()._action_confirm()
        
        for order in self:
            if order.is_window_order and not order.production_id:
                order._create_production_order()
        
        return result

    def _create_production_order(self):
        """Создать производственный заказ"""
        if not self.is_window_order:
            return
        
        # Найти или создать продукт окна
        product = self._get_or_create_window_product()
        
        # Создать BOM если нужно
        bom = self._get_or_create_bom(product)
        
        # Создать производственный заказ
        production = self.env['mrp.production'].create({
            'product_id': product.id,
            'product_qty': sum(self.order_line.filtered(lambda l: l.product_id == product).mapped('product_uom_qty')) or 1.0,
            'product_uom_id': product.uom_id.id,
            'bom_id': bom.id if bom else False,
            'origin': self.name,
            'window_order_id': self.id,
        })
        
        self.production_id = production.id
        
        # Обновить лид
        if self.opportunity_id:
            self.opportunity_id.production_id = production.id

    def _get_or_create_window_product(self):
        """Получить или создать продукт окна"""
        # Ищем существующий продукт по параметрам
        product = self.env['product.product'].search([
            ('is_window_product', '=', True),
            ('window_profile_type', '=', self.window_profile_type),
            ('window_glass_unit_type', '=', self.window_glass_unit_type),
        ], limit=1)
        
        if not product:
            # Создаем новый продукт
            profile_name = dict(self._fields['window_profile_type'].selection).get(self.window_profile_type, '') if self.window_profile_type else ''
            glass_name = dict(self._fields['window_glass_unit_type'].selection).get(self.window_glass_unit_type, '') if self.window_glass_unit_type else ''
            product_name = f'Окно {profile_name} {glass_name}'.strip()
            
            product = self.env['product.product'].create({
                'name': product_name or 'Окно',
                'type': 'product',
                'categ_id': self.env.ref('product.product_category_all').id,
                'is_window_product': True,
                'window_profile_type': self.window_profile_type,
                'window_glass_unit_type': self.window_glass_unit_type,
                'sale_ok': True,
                'purchase_ok': False,
            })
        
        return product

    def _get_or_create_bom(self, product):
        """Получить или создать BOM для продукта"""
        bom = self.env['mrp.bom'].search([
            ('product_id', '=', product.id),
        ], limit=1)
        
        if not bom:
            # Ищем BOM по шаблону продукта
            bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ], limit=1)
        
        if not bom:
            # Создаем простой BOM (можно расширить логику)
            bom = self.env['mrp.bom'].create({
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_qty': 1.0,
                'product_uom_id': product.uom_id.id,
                'type': 'normal',
            })
        
        return bom

    def action_create_contract(self):
        """Создать договор из КП"""
        self.ensure_one()
        
        if self.state not in ['sale', 'done']:
            raise UserError(_('Договор можно создать только из подтвержденного заказа.'))
        
        # Обновить статус лида
        if self.opportunity_id:
            self.opportunity_id.contract_id = self.id
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/sale.order/{self.id}/contract_pdf/{self.contract_pdf_name}',
            'target': 'new',
        }

    def action_print_offer(self):
        """Печать коммерческого предложения"""
        return self.env.ref('window_offer.action_report_offer').report_action(self)

    def action_print_contract(self):
        """Печать договора"""
        return self.env.ref('window_offer.action_report_contract').report_action(self)

    def action_print_specification(self):
        """Печать спецификации"""
        return self.env.ref('window_offer.action_report_specification').report_action(self)

    def action_print_act(self):
        """Печать акта выполненных работ"""
        return self.env.ref('window_offer.action_report_act').report_action(self)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    window_width = fields.Float(
        string='Ширина (мм)',
        digits=(16, 1),
    )
    window_height = fields.Float(
        string='Высота (мм)',
        digits=(16, 1),
    )
    window_area = fields.Float(
        string='Площадь (м²)',
        compute='_compute_window_area',
        store=True,
        digits=(16, 2),
    )

    @api.depends('window_width', 'window_height')
    def _compute_window_area(self):
        for line in self:
            if line.window_width and line.window_height:
                line.window_area = (line.window_width * line.window_height) / 1000000  # мм² в м²
            else:
                line.window_area = 0.0

