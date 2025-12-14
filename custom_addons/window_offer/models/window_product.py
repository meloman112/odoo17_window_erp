# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_window_product = fields.Boolean(
        string='Продукт окна',
        default=False,
    )
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
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_window_product = fields.Boolean(
        string='Продукт окна',
        related='product_tmpl_id.is_window_product',
        store=True,
    )
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
        related='product_tmpl_id.window_profile_type',
        store=True,
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
        related='product_tmpl_id.window_glass_unit_type',
        store=True,
    )

