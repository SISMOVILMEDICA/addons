from odoo import _, api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    specialties_ids = fields.Many2many(related="employee_id.specialties_ids")
