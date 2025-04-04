from odoo import models


class PurchaseOrder(models.Model):
    """Inherits the purchase order for disable the follower"""
    _inherit = 'purchase.order'

    def button_confirm(self):
        """Check whether 'Disable Follower' is enabled.
            If enabled, unsubscribe the user_id from the followers list."""
        result = super(PurchaseOrder, self).button_confirm()

        # Vérifier si le paramètre "follower_restrict.disable_followers" est activé
        if self.env['ir.config_parameter'].sudo().get_param(
                "follower_restrict.disable_followers"):

            # Récupérer le partenaire associé au user_id
            user_partner = self.user_id.partner_id.id if self.user_id else False

            # Si un partenaire est trouvé pour le user_id, le désabonner
            if user_partner:
                self.message_unsubscribe([user_partner])

        return result
