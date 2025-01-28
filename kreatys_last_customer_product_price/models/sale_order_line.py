from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    last_product_price = fields.Float(
        string='Dernier prix pratiqué', readonly=True)

    @api.onchange('product_id', 'order_partner_id')
    def _compute_last_product_price(self):
        for line in self:
            if line.product_id and line.order_id.partner_id:
                last_product_price = 0.0

                # Recherche des derniers devis du client
                devis = self.env['sale.order'].search([
                    ('partner_id', '=', line.order_partner_id.id),
                    ('state', 'in', ['draft', 'sent', 'sale']),
                ], order='date_order desc', limit=1)

                # Si des devis sont trouvés, recherche du dernier prix pratiqué
                if devis:
                    order_line = devis.order_line.filtered(
                        lambda l: l.product_id == line.product_id)
                    if order_line:
                        last_product_price = order_line[0].price_unit

                # Sinon, recherche des dernières factures du client
                else:
                    factures = self.env['account.move'].search([
                        ('partner_id', '=', line.order_partner_id.id),
                        ('state', '=', 'posted'),
                        ('move_type', '=', 'out_invoice'),
                    ], order='date desc', limit=1)

                    # Si des factures sont trouvées, recherche du dernier prix pratiqué
                    if factures:
                        invoice_line = factures[0].invoice_line_ids.filtered(
                            lambda l: l.product_id == line.product_id)
                        if invoice_line:
                            last_product_price = invoice_line[0].price_unit

                line.last_product_price = last_product_price
