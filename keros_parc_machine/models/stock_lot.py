from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    machine_count = fields.Integer(
        string="Parc Machine",
        compute="_compute_machine_count",
    )

    def _compute_machine_count(self):
        for lot in self:
            lot.machine_count = self.env['parc.machine'].search_count(
                [('serial_number', '=', lot.id)])

    def action_view_machines(self):
        self.ensure_one()
        machines = self.env['parc.machine'].search(
            [('serial_number', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Machines Associées',
            'view_mode': 'list,kanban,form',
            'res_model': 'parc.machine',
            'domain': [('id', 'in', machines.ids)],
            # Désactive la création de nouvelles machines depuis cette vue
            'context': {'create': False},
        }
