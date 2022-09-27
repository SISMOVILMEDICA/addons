from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_register_payment(self):
        return {
            "name": _("Register Voucher"),
            "res_model": "account.voucher.wizard",
            "view_mode": "form",
            "context": {
                "active_model": "account.move",
                "active_ids": self.ids,
                "default_active_bool": len(self.ids) > 1,
                "default_amount": self and self[0].amount_residual or False,
                "default_currency_id": self and self[0].currency_id.id or False,
                "default_voucher_reference": self and self[0].name or False,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    voucher_line_id = fields.Many2one(comodel_name="account.move.line", string="Voucher Line")
