from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def update_prices_based_on_pricelist(self):
        for order in self:
            # if not order.pricelist_id:
            #     raise UserError(
            #         "Aucune liste de prix n'est définie sur cette commande.")

            for line in order.order_line:
                product = line.product_id
                quantity = line.product_uom_qty or 1.0

                if not product:
                    continue

                best_price = None
                category_price = None
                today = fields.Datetime.now()
                product_uom = product.uom_id

                for item in order.pricelist_id.item_ids:
                    applies = False

                    if item.applied_on == '3_global':
                        applies = True
                    elif item.applied_on == '2_product_category':
                        applies = product.categ_id == item.categ_id
                    elif item.applied_on == '1_product':
                        applies = product.product_tmpl_id == item.product_tmpl_id
                    elif item.applied_on == '0_product_variant':
                        applies = product == item.product_id

                    if applies:
                        if item.min_quantity > 0 and quantity < item.min_quantity:
                            continue

                        if item.date_start and item.date_start > today:
                            continue
                        if item.date_end and item.date_end < today:
                            continue

                        if item.compute_price == 'fixed':
                            price = item.fixed_price
                        elif item.compute_price == 'percentage':
                            price = product.list_price * \
                                (1 - item.percent_price / 100)
                        elif item.compute_price == 'formula':
                            base_price = product.list_price if item.base == 'list_price' \
                                else product.standard_price if item.base == 'standard_price' \
                                else 0
                            price = (
                                base_price * (1 + item.price_discount / 100)) + item.price_surcharge

                        if item.applied_on == '2_product_category':
                            category_price = price
                        elif best_price is None or price < best_price:
                            best_price = price

                if category_price is not None and (best_price is None or category_price < best_price):
                    line.write({'price_unit': category_price})
                elif best_price is not None:
                    line.write({'price_unit': best_price})
                # else:
                #     raise UserError(
                #         f"Aucun prix applicable trouvé pour le produit '{product.name}'.")
