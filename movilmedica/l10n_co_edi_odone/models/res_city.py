from odoo import fields, models


class City(models.Model):
    _inherit = "res.city"

    l10n_co_edi_code = fields.Char("Código EDI")
