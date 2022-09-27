from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TaxType(models.Model):
    _name = "l10n_co_edi.tax.type"
    _description = "Colombian EDI Tax Type"

    name = fields.Char(string="Name")
    description = fields.Char(string="Descripción")
    code = fields.Char(string="Código", required=True)
    retention = fields.Boolean(string="Retencion")
