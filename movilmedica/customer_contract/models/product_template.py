from datetime import datetime

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_cums = fields.Boolean(string="Es CUMS")
    atc = fields.Char(string="ATC")
    expedient = fields.Char(string="Expediente")
    consecutive = fields.Char(string="Consecutivo")

    @api.onchange("atc", "expedient", "consecutive", "is_cums")
    def _onchange_name_cums(self):
        for record in self:
            if not record.is_cums:
                continue
            record.name = ""
            for i, field in enumerate(["atc", "expedient", "consecutive"]):
                value = getattr(record, field)
                record.name += "-" if i == 2 and value else ""
                record.name += value if value else ""
