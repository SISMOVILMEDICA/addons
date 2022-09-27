from odoo import api, fields, models


class CustomerContractDiagnostic(models.Model):
    _name = "customer.contract.diagnostic"
    _description = "Ayudas diagnosticas"

    active = fields.Boolean("Activo", default=True)
    name = fields.Char("Nombre", required=True)
    code = fields.Char("Codigo", required=True)
