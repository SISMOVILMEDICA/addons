from odoo import api, fields, models


class ClinicHistory(models.Model):
    _inherit = "clinic.history"

    age = fields.Integer(
        string="Edad",
        compute="_compute_patient_age_years",
        store=True,
    )

    @api.depends("partner_id.patient_age_years")
    def _compute_patient_age_years(self):
        for history in self:
            if history.age:
                continue
            if not history.partner_id:
                history.age = 0
                continue
            history.age = history.partner_id.patient_age_years

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     if res.partner_id:
    #         res.age = res.partner_id.patient_age_years
    #     return res
