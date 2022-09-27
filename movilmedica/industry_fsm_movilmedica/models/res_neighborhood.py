from odoo import api, fields, models


class ResNeighborhood(models.Model):
    _name = "res.neighborhood"
    _description = "Neighborhoods"

    name = fields.Char("Name", required=True)
    locality_id = fields.Many2one("res.locality", "Locality", required=True)
