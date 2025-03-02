from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    machine_count = fields.Integer(
        string="Machines", compute='compute_machine_count', default=0)

    def compute_machine_count(self):
        for record in self:
            record.machine_count = self.env['parc.machine'].search_count(
                [('partner_id', '=', record.id)])

    def action_get_machines_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Machines',
            'view_mode': 'list,form,kanban',
            'res_model': 'parc.machine',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id, 'create': True}
        }
