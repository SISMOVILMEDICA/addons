from odoo import fields, models


class IrSequenceDateRange(models.Model):
    _inherit = "ir.sequence.date_range"

    edi_resolution = fields.Char(string="Resolución")
    number_from = fields.Integer(string="Número inicial", default=False)
    number_to = fields.Integer(string="Número final", default=False)
    active_resolution = fields.Boolean(string="Resolución Activa")
    prefix = fields.Char(string="Prefix")
