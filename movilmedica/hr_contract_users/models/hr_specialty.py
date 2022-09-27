from odoo import api, fields, models


class HrSpecialty(models.Model):
    _name = "hr.specialty"
    _description = "Specialty"
    _order = "sequence"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    sequence = fields.Integer("Sequence")
