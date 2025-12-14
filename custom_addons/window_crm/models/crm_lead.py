# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def write(self, vals):
        """Проверка прав Call Center при изменении"""
        if self.env.user.has_group('window_crm.group_call_center'):
            # Call Center не может перемещать лиды после стадии "Замер"
            if 'stage_id' in vals:
                stage_measure = self.env['crm.stage'].search([
                    ('name', '=', 'Назначен замер')
                ], limit=1)
                if stage_measure:
                    for lead in self:
                        if lead.stage_id.sequence >= stage_measure.sequence:
                            raise UserError(_('Call Center не может перемещать лиды после стадии "Замер".'))
        
        return super().write(vals)

    def unlink(self):
        """Проверка прав Call Center при удалении"""
        if self.env.user.has_group('window_crm.group_call_center'):
            raise UserError(_('Call Center не может удалять лиды.'))
        return super().unlink()

