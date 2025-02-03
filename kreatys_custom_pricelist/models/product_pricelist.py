from odoo import models, fields


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _compute_price_rule(
            self, products, quantity, currency=None, uom=None, date=False, compute_price=True,
            **kwargs
    ):

        self and self.ensure_one()  # self is at most one record
        currency = currency or self.currency_id or self.env.company.currency_id
        currency.ensure_one()
        if not products:
            return {}
        if not date:
            # Used to fetch pricelist rules and currency rates
            date = fields.Datetime.now()
        # Fetch all rules potentially matching specified products/templates/categories and date
        rules = self._get_applicable_rules(products, date, **kwargs)
        results = {}
        for product in products:
            suitable_rule = self.env['product.pricelist.item']
            product_uom = product.uom_id
            # If no uom is specified, fall back on the product uom
            target_uom = uom or product_uom
            # Compute quantity in product uom because pricelist rules are specified
            # w.r.t product default UoM (min_quantity, price_surchage, ...)
            if target_uom != product_uom:
                qty_in_product_uom = target_uom._compute_quantity(
                    quantity, product_uom, raise_if_failure=False
                )
            else:
                qty_in_product_uom = quantity
            best_price = float('inf')
            for rule in rules:
                if rule._is_applicable_for(product, qty_in_product_uom):
                    price = rule._compute_price(
                        product, quantity, target_uom, date=date, currency=currency)
                    if price < best_price:
                        best_price = price
                        suitable_rule = rule
            if best_price == float('inf'):
                # If no applicable rule was found, use the list price as the default price
                best_price = product.list_price
                suitable_rule = self.env['product.pricelist.item']
            if compute_price:
                price = best_price
            else:
                # Skip price computation when only the rule is requested.
                price = 0.0
            results[product.id] = (price, suitable_rule.id)
        return results


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_sales_prices(self, website):
        if not self:
            return {}
        pricelist = website.pricelist_id
        currency = website.currency_id
        fiscal_position = website.fiscal_position_id.sudo()
        date = fields.Date.context_today(self)
        pricelist_prices = pricelist._compute_price_rule(self, 1.0)
        comparison_prices_enabled = self.env.user.has_group(
            'website_sale.group_product_price_comparison')
        res = {}
        for template in self:
            pricelist_price, pricelist_rule_id = pricelist_prices[template.id]
            product_taxes = template.sudo().taxes_id._filter_taxes_by_company(self.env.company)
            taxes = fiscal_position.map_tax(product_taxes)
            base_price = None
            template_price_vals = {
                'price_reduce': self._apply_taxes_to_price(
                    pricelist_price, currency, product_taxes, taxes, template, website=website,
                ),
            }
            pricelist_item = template.env['product.pricelist.item'].browse(
                pricelist_rule_id)
            if pricelist_item._show_discount_on_shop():
                pricelist_base_price = pricelist_item._compute_price_before_discount(
                    product=template,
                    quantity=1.0,
                    date=date,
                    uom=template.uom_id,
                    currency=currency,
                )
                if currency.compare_amounts(pricelist_base_price, pricelist_price) == 1:
                    base_price = pricelist_base_price
                    template_price_vals['base_price'] = self._apply_taxes_to_price(
                        base_price, currency, product_taxes, taxes, template, website=website,
                    )
            if not base_price and comparison_prices_enabled and template.compare_list_price:
                template_price_vals['base_price'] = template.currency_id._convert(
                    template.compare_list_price,
                    currency,
                    self.env.company,
                    date,
                    round=False,
                )
            res[template.id] = template_price_vals
        return res
