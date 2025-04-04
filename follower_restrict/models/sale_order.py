from odoo import models


class SaleOrder(models.Model):
    """Inherits the sale order for disable the follower"""
    _inherit = 'sale.order'

    def action_confirm(self):
        """Check whether 'Disable Follower' is enabled.
            If enabled, unsubscribe the user_id from the followers list."""
        result = super(SaleOrder, self).action_confirm()

        # Vérifier si le paramètre "follower_restrict.disable_followers" est activé
        if self.env['ir.config_parameter'].sudo().get_param(
                "follower_restrict.disable_followers"):

            # Récupérer le partenaire associé au user_id
            user_partner = self.user_id.partner_id.id if self.user_id else False

            # Si un partenaire est trouvé pour le user_id, le désabonner
            if user_partner:
                self.message_unsubscribe([user_partner])

        return result
