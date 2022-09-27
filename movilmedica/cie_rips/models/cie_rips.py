from odoo import api, fields, models

SEX = [("H", "Hombre"), ("M", "Mujer"), ("A", "Ambos")]


class HrLeaveCause(models.Model):
    _name = "cie.rips"
    _description = "CLASIFICACIÓN ESTADÍSTICA INTERNACIONAL DE ENFERMEDADES"

    name = fields.Char(
        string="Nombre", compute="_compute_name", store=True, index=True, readonly=True
    )
    description = fields.Char(string="Descripción")
    code = fields.Char(string="Código")
    symbol = fields.Char(string="Símbolo")
    sex = fields.Selection(string="Sexo", selection=SEX)
    lower_limit = fields.Integer(string="Límite inferior")
    upper_limit = fields.Integer(string="Límite superior")

    @api.depends("code", "description")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.code} - {record.description}"
