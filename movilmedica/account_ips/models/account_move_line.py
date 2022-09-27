from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    copago = fields.Float(string="Copago", digits="Product Price")
