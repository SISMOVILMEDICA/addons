from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    confirm_bool = fields.Boolean("Confirm bool", compute="_compute_confirm_bool")

    moderating_fee = fields.Float(string="Cuota Moderadora", digits="Product Price")

    patient_name = fields.Char(string="Nombre Paciente")
    patient_identification_type_id = fields.Many2one(
        "l10n_latam.identification.type", string="Tipo de identificación"
    )
    patient_vat = fields.Char(string="Identificación")
    patient_street = fields.Char(string="Dirección")
    patient_city_id = fields.Many2one("res.city", string="Ciudad")
    patient_state_id = fields.Many2one("res.country.state", string="Departamento")
    patient_country_id = fields.Many2one(
        "res.country", string="País", default=lambda self: self.env.ref("base.co")
    )
    patient_phone = fields.Char(string="Teléfono")
    patient_modality = fields.Char(string="Modalidad")
    date_service = fields.Date(string="Fecha del Servicio", default=fields.Date.today)
    regime = fields.Char(string="Régimen")

    @api.depends(
        "move_type",
        "invoice_line_ids",
        "invoice_line_ids.product_id",
        "patient_vat",
        "invoice_date",
    )
    def _compute_confirm_bool(self):
        for move in self:
            confirm_bool = False
            if move.move_type == "out_invoice":
                for line in move.invoice_line_ids:
                    domain = [
                        ("product_id", "=", line.product_id.id),
                        ("move_id.patient_vat", "=", move.patient_vat),
                        ("move_id.invoice_date", "=", move.invoice_date),
                    ]
                    count = self.env["account.move.line"].search_count(domain)
                    confirm_bool = True if count > 1 else False
            else:
                confirm_bool = False
            move.update({"confirm_bool": confirm_bool})

    @api.onchange("patient_city_id", "patient_state_id")
    def _onchange_location_patient(self):
        if self.patient_city_id:
            self.patient_state_id = self.patient_city_id.state_id.id
            self.patient_country_id = self.patient_city_id.country_id.id
        if self.patient_state_id:
            return {"domain": {"patient_city_id": [("state_id", "=", self.patient_state_id.id)]}}
