from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ParcMachine(models.Model):
    _name = 'parc.machine'
    _description = 'Parc Machine'

    name = fields.Char(string='Nom', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partenaire', store=True)
    serial_number = fields.Many2one(
        'stock.lot', string='Numéro de Série', required=True)
    manufacturer = fields.Many2one('res.partner', string='Fabricant')
    acquisition_date = fields.Date(
        string='Date d\'Acquisition', compute='_compute_acquisition_date', store=True)
    warranty_start_date = fields.Date(string='Début Garantie')
    warranty_end_date = fields.Date(string='Fin Garantie')
    rma_warranty_end_date = fields.Date(string='Fin Garantie si RMA + 1 an')
    status = fields.Selection([
        ('sav', 'SAV'),
        ('a_revenir', 'À revenir'),
        ('pret', 'Prêt'),
        ('echange_standard', 'Échange standard'),
        ('reserve_location', 'Réservé location'),
        ('ram', 'RAM'),
        ('hors_service', 'Hors Service')
    ], string='Statut')
    loan_location = fields.Char(string='Lieu du prêt')
    flash_count = fields.Integer(string='Nombre de Flashs')
    flash_count_date = fields.Date(string='Date de relevé du nombre de flashs')
    last_delivery_date = fields.Date(string='Date d\'expédition')
    delivery_order_number = fields.Char(string='Numéro du bon de livraison')
    ram_number = fields.Char(string='Numéro du RAM')
    comment = fields.Text(string='Commentaires')
    location_id = fields.Many2one(
        'stock.location', string='Emplacement de stockage')
    product_id = fields.Many2one(
        'product.product', string='Référence de l\'article', related='serial_number.product_id', store=True)
    rma_number = fields.Char(string='N° de RMA')
    color = fields.Integer(string='Couleur Index', default=0)

    @api.depends('serial_number')
    def _compute_acquisition_date(self):
        for record in self:
            _logger.debug(
                f"Computing acquisition date for record {record.id} with serial number {record.serial_number.name}")
            if record.serial_number:
                # Recherche de la facture d'achat la plus ancienne contenant le lot
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

    @api.onchange('status')
    def _onchange_status(self):
        if self.status == 'hors_service':
            self.send_email_to_mariette()
            _logger.info(
                f"Status changed to 'Hors Service' for record {self.id}")

    def send_email_to_mariette(self):
        template = self.env.ref(
            'keros_parc_machine.email_template_hors_service')
        if template:
            template.send_mail(self.id, force_send=True)
            _logger.info(f"Email sent to Mariette for record {self.id}")
        else:
            _logger.error(
                "Email template 'keros_parc_machine.email_template_hors_service' not found")

    def action_send_to_repair(self):
        for record in self:
            _logger.debug(f"Sending machine {record.name} to repair")
            if record.product_id:
                # Création de la demande de réparation
                repair_vals = {
                    'product_id': record.product_id.id,
                    'product_qty': 1.0,
                    'product_uom': record.product_id.uom_id.id,
                    'name': f"Réparation - {record.name}",
                    'lot_id': record.serial_number.id,
                    'location_id': record.location_id.id or self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': record.location_id.id or self.env.ref('stock.stock_location_stock').id,
                }
                repair_order = self.env['repair.order'].create(repair_vals)
                _logger.info(
                    f"Repair order {repair_order.name} created for machine {record.name}")

                # Changer le statut de la machine (optionnel)
                record.status = 'sav'

                # Ouvrir la vue formulaire de la réparation créée
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Demande de Réparation',
                    'view_mode': 'form',
                    'res_model': 'repair.order',
                    'res_id': repair_order.id,
                    'target': 'current',  # Ouvre la vue dans une nouvelle fenêtre
                }
            else:
                _logger.error(
                    f"No product associated with machine {record.name}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erreur',
                        'message': 'Aucun produit associé à cette machine.',
                        'sticky': False,
                    }
                }

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

# REPAIR ORDERS
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
