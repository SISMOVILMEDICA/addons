from odoo import fields, models


class ClinicHistoryRecommendation(models.Model):
    _name = "clinic.history.recommendation"
    _description = "Recommendations"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    recommendation = fields.Text("Recommendation", required=True)
