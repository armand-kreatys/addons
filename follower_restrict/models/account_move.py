from odoo import models


class AccountMove(models.Model):
    """Inherits the account.move for restrict follower while invoicing"""
    _inherit = 'account.move'

    def action_post(self):
        """Check whether 'Disable Follower' is enabled.
            If enabled, unsubscribe the user_id from the followers list."""
        result = super(AccountMove, self).action_post()

        # Vérifier si le paramètre "follower_restrict.disable_followers" est activé
        if self.env['ir.config_parameter'].sudo().get_param(
                "follower_restrict.disable_followers"):

            # Récupérer le partenaire associé au user_id
            user_partner = self.invoice_user_id.partner_id.id if self.invoice_user_id else False

            # Si un partenaire est trouvé pour le user_id, le désabonner
            if user_partner:
                self.message_unsubscribe([user_partner])

        return result
