from odoo import _, api, fields, models


class HrSpecialty(models.Model):
    _inherit = "hr.specialty"

    action_char = fields.Char("View", default="clinic_history.action_clinic_history_form")
