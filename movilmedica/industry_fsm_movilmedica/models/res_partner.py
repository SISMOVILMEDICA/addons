from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(
        selection_add=[("patient", "Patient")], ondelete={"patient": "set default"}
    )

    patient_affiliation = fields.Selection(
        [("contributor", "Contributor"), ("beneficiary", "Beneficiary")], "Affiliation type"
    )
    patient_gender = fields.Selection([("male", "Hombre"), ("female", "Mujer")], string="Genero")
    patient_uom_id = fields.Many2one("uom.uom", "UoM")
    patient_martial_status = fields.Selection(
        selection=[
            ("single", "Soltero/a"),
            ("married", "Casado/a"),
            ("widowed", "Viudo/a"),
            ("free_union", "Unión libre"),
        ],
        string="Estado civil",
    )
    patient_birthdate = fields.Date("Fecha de nacimiento")
    patient_age_years = fields.Integer(
        string="Edad",
        compute="_compute_patient_age_years",
    )

    @api.depends("patient_birthdate")
    def _compute_patient_age_years(self):
        for partner in self:
            if not partner.patient_birthdate:
                partner.patient_age_years = 0
                continue
            today = fields.Date.today()
            partner.patient_age_years = relativedelta(today, partner.patient_birthdate).years

    locality_id = fields.Many2one("res.locality", "Locality")
    neighborhood_id = fields.Many2one("res.neighborhood", "Neighborhood")
