from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.template'

    manufacturer = fields.Many2one(
        'res.partner', string='Fabricant', help="Fabricant du produit"
    )
