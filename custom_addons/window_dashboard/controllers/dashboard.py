# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from odoo import fields


class WindowDashboard(http.Controller):

    @http.route('/window_dashboard/get_sales_funnel', type='json', auth='user')
    def get_sales_funnel(self, **kwargs):
        """Получить данные воронки продаж"""
        stages = request.env['crm.stage'].search([], order='sequence')
        funnel_data = []
        
        for stage in stages:
            leads_count = request.env['crm.lead'].search_count([
                ('stage_id', '=', stage.id),
                ('type', '=', 'opportunity')
            ])
            funnel_data.append({
                'stage': stage.name,
                'count': leads_count,
            })
        
        return funnel_data

    @http.route('/window_dashboard/get_production_plan', type='json', auth='user')
    def get_production_plan(self, **kwargs):
        """Получить производственный план"""
        productions = request.env['mrp.production'].search([
            ('state', 'in', ['confirmed', 'progress', 'to_close'])
        ])
        
        plan_data = []
        for prod in productions:
            plan_data.append({
                'name': prod.name,
                'product': prod.product_id.name,
                'qty': prod.product_qty,
                'state': dict(prod._fields['state'].selection).get(prod.state),
                'date_start': prod.date_start.strftime('%d.%m.%Y') if prod.date_start else '',
            })
        
        return plan_data

    @http.route('/window_dashboard/get_measurer_kpi', type='json', auth='user')
    def get_measurer_kpi(self, **kwargs):
        """Получить KPI замерщиков"""
        date_from = fields.Datetime.now() - timedelta(days=30)
        measures = request.env['window.measure'].search([
            ('date_done', '>=', date_from)
        ])
        
        kpi_data = {}
        for measure in measures:
            measurer = measure.measurer_id.name
            if measurer not in kpi_data:
                kpi_data[measurer] = {
                    'total': 0,
                    'done': 0,
                    'avg_time': 0,
                }
            
            kpi_data[measurer]['total'] += 1
            if measure.state == 'done':
                kpi_data[measurer]['done'] += 1
                if measure.date_planned and measure.date_done:
                    delta = measure.date_done - measure.date_planned
                    kpi_data[measurer]['avg_time'] += delta.total_seconds() / 3600
        
        # Вычислить среднее время
        for measurer in kpi_data:
            if kpi_data[measurer]['done'] > 0:
                kpi_data[measurer]['avg_time'] = kpi_data[measurer]['avg_time'] / kpi_data[measurer]['done']
        
        return kpi_data

    @http.route('/window_dashboard/get_installer_kpi', type='json', auth='user')
    def get_installer_kpi(self, **kwargs):
        """Получить KPI монтажников"""
        date_from = fields.Datetime.now() - timedelta(days=30)
        tasks = request.env['project.task'].search([
            ('is_installation_task', '=', True),
            ('date_deadline', '>=', date_from)
        ])
        
        kpi_data = {}
        for task in tasks:
            installer = task.installer_team_id.name or 'Не назначен'
            if installer not in kpi_data:
                kpi_data[installer] = {
                    'total': 0,
                    'completed': 0,
                    'avg_time': 0,
                }
            
            kpi_data[installer]['total'] += 1
            if task.installation_state == 'act':
                kpi_data[installer]['completed'] += 1
        
        return kpi_data

    @http.route('/window_dashboard/get_lead_processing_time', type='json', auth='user')
    def get_lead_processing_time(self, **kwargs):
        """Получить средний срок обработки лида"""
        date_from = fields.Datetime.now() - timedelta(days=90)
        leads = request.env['crm.lead'].search([
            ('create_date', '>=', date_from),
            ('date_closed', '!=', False),
        ])
        
        total_time = 0
        count = 0
        
        for lead in leads:
            if lead.create_date and lead.date_closed:
                delta = lead.date_closed - lead.create_date
                total_time += delta.total_seconds() / 86400  # дни
                count += 1
        
        avg_time = total_time / count if count > 0 else 0
        
        return {
            'avg_days': round(avg_time, 1),
            'total_leads': count,
        }

    @http.route('/window_dashboard/get_order_profitability', type='json', auth='user')
    def get_order_profitability(self, **kwargs):
        """Получить доходность заказов"""
        date_from = fields.Datetime.now() - timedelta(days=30)
        orders = request.env['sale.order'].search([
            ('is_window_order', '=', True),
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', date_from)
        ])
        
        total_revenue = sum(orders.mapped('amount_total'))
        total_count = len(orders)
        avg_order = total_revenue / total_count if total_count > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'total_orders': total_count,
            'avg_order': round(avg_order, 2),
        }

