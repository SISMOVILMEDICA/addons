from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    voucher_reconcile_amount = fields.Monetary(
        string="Amount reconcile",
        related="company_id.voucher_reconcile_amount",
        help="Maximum value in crosses",
        readonly=False,
    )
