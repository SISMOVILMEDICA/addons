from odoo import api, fields, models


class HrIllness(models.Model):
    _name = "hr.illness"
    _description = "Illness"
    _order = "sequence"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    sequence = fields.Integer("Sequence")
