from datetime import datetime
from email.policy import default

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class Contact(models.Model):
    _inherit = "res.partner"

    date_b = fields.Date(string="Fecha de nacimiento")

    @api.onchange("date_b")
    def _get_age(self):
        for line in self:
            edad = relativedelta(
                fields.Date.from_string(fields.date.today()), fields.Date.from_string(line.date_b)
            )
            line.age1 = edad.years

    def _get_country(self):
        country_id = self.env["res.country"].search([("code", "=", "CO")], limit=1)
        return country_id

    country_id = fields.Many2one("res.country", default=_get_country)


class Contract(models.Model):
    _name = "contract1"

    name = fields.Char(string="Nombre")


class CustomerContract(models.Model):
    _inherit = "customer.contract"

    contract_ids1 = fields.Many2many("contract1", string="Convenios")
