from odoo import api, fields, models


class HrAllergy(models.Model):
    _name = "hr.allergy"
    _description = "Allergy"
    _order = "sequence"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    sequence = fields.Integer("Sequence")
