from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ParcMachine(models.Model):
    _name = 'parc.machine'
    _description = 'Parc Machine'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Client', store=True, tracking=True)
    serial_number = fields.Many2one(
        'stock.lot', string='Numéro de Série', required=True)
    manufacturer = fields.Many2one(
        related='product_id.manufacturer',
        string='Fabricant',
        store=True,
        readonly=True
    )
    acquisition_date = fields.Date(
        string='Date d\'Acquisition', compute='_compute_acquisition_date', store=True)
    warranty_start_date = fields.Date(string='Début Garantie')
    warranty_end_date = fields.Date(string='Fin Garantie')
    keros_warranty_end_date = fields.Date(string='Fin Garantie Keros')
    rma_warranty_end_date = fields.Date(string='Fin Garantie si RMA + 1 an')
    status = fields.Selection([
        ('sav', 'SAV'),
        ('a_revenir', 'À revenir'),
        ('pret', 'Prêt'),
        ('rma', 'RMA'),
        ('echange_standard', 'Échange standard'),
        ('reserve_location', 'Réservé location'),
        ('hors_service', 'Hors Service')
    ], string='Statut', default='pret')
    loan_location = fields.Char(string='Lieu du prêt')
    flash_count = fields.Integer(string='Nombre de Flashs', tracking=True)
    flash_count_date = fields.Date(
        string='Date de relevé du nombre de flashs', tracking=True)
    last_delivery_date = fields.Date(
        string='Date d\'expédition', compute='_compute_last_delivery', store=True, tracking=True)
    delivery_order_number = fields.Char(
        string='Numéro du bon de livraison', compute='_compute_last_delivery', store=True, tracking=True)
    comment = fields.Text(string='Commentaires')
    location_id = fields.Many2one(
        related='serial_number.location_id',
        string='Emplacement de stockage',
        store=True,
        readonly=True
    )
    product_id = fields.Many2one(
        'product.product', string='Référence de l\'article', related='serial_number.product_id', store=True)
    rma_number = fields.Char(string='N° de RMA')
    color = fields.Integer(string='Couleur Index', default=0)

    @api.depends('serial_number')
    def _compute_last_delivery(self):
        for record in self:
            delivery_move = self.env['stock.move'].search([
                ('product_id', '=', record.product_id.id),
                ('picking_type_id.code', '=', 'outgoing'),  # Mouvement de sortie
                ('move_line_ids.lot_id', '=', record.serial_number.id)
            ], order='date desc', limit=1)
            if delivery_move:
                record.last_delivery_date = delivery_move.date
                record.warranty_start_date = record.last_delivery_date
                record.delivery_order_number = delivery_move.picking_id.name
            else:
                record.last_delivery_date = False
                record.delivery_order_number = False

    @api.depends('serial_number')
    def _compute_acquisition_date(self):
        for record in self:
            _logger.debug(
                f"Computing acquisition date for record {record.id} with serial number {record.serial_number.name}")
            if record.serial_number:
                # Recherche de la l'achat le plus ancienne contenant le lot/numéro de série
                purchase_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('move_ids.move_line_ids.lot_id', '=', record.serial_number.id)
                ], order='date_order asc', limit=1)
                if purchase_line:
                    record.acquisition_date = purchase_line.order_id.date_order
                    _logger.info(
                        f"Found acquisition date {record.acquisition_date} from purchase order {purchase_line.order_id.name}")
                else:
                    record.acquisition_date = False
                    _logger.info(
                        "No purchase order found for the serial number")
            else:
                record.acquisition_date = False
                _logger.info("Serial number not set")

    @api.onchange('serial_number')
    def _onchange_serial_number(self):
        if self.serial_number:
            _logger.debug(
                f"Processing onchange for serial number {self.serial_number.name}")
            # Recherche de la location en cours
            location_line = self.env['stock.move.line'].search([
                ('product_id', '=', self.product_id.id),
                ('state', '=', 'assigned'),
                ('lot_id', '=', self.serial_number.id)
            ], limit=1)
            if location_line:
                self.loan_location = location_line.picking_id.partner_id.street
                _logger.info(f"Loan location found: {self.loan_location}")
            else:
                self.loan_location = False
                _logger.info("No ongoing loan location found")
            if self.product_id:
                self.name = self.product_id.name
                _logger.info(f"Nom du produit: {self.name}")

    def action_view_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Machine',
            'view_mode': 'form',
            'res_model': 'parc.machine',
            'res_id': self.id,
            'target': 'current',
        }

    # Repair orders
    repair_part_count = fields.Integer(
        string="Repair Parts", compute="_compute_repair_counts"
    )
    in_repair_count = fields.Integer(
        string="To Do", compute="_compute_repair_counts"
    )
    repaired_count = fields.Integer(
        string="Done", compute="_compute_repair_counts"
    )

    @api.depends('serial_number')
    def _compute_repair_counts(self):
        for record in self:
            if record.serial_number:
                record.repair_part_count = record.serial_number.repair_part_count
                record.in_repair_count = record.serial_number.in_repair_count
                record.repaired_count = record.serial_number.repaired_count
            else:
                record.repair_part_count = 0
                record.in_repair_count = 0
                record.repaired_count = 0

    def serial_number_action_view_ro(self):
        return self.serial_number.action_view_ro()

    def serial_number_action_lot_open_repairs(self):
        return self.serial_number.action_lot_open_repairs()
