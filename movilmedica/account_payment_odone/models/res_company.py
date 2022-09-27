from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    voucher_reconcile_amount = fields.Monetary(
        string="Amount reconcile", help="Maximum value in crosses"
    )
