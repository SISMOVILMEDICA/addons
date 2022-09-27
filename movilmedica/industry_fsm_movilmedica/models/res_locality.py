from odoo import api, fields, models


class ResLocality(models.Model):
    _name = "res.locality"
    _description = "Localities"

    name = fields.Char("Name", required=True)
    city_id = fields.Many2one("res.city", "City", required=True)
