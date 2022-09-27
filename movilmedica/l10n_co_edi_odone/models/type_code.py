from odoo import _, api, fields, models


class TypeCode(models.Model):
    _name = "l10n_co_edi.type_code"
    _description = "Colombian EDI Type Code"

    name = fields.Char(required=True)
    description = fields.Char(required=True)
    type = fields.Selection(
        [
            ("representation", "Representation"),
            ("obligation", "Obligation"),
            ("customs", "Customs"),
            ("establishment", "Establishment"),
        ],
        required=True,
    )
    is_required_dian = fields.Boolean(string="Vigente para FE")

    def name_get(self):
        res = []
        for record in self:
            name = "[{}] {}".format(record.name, record.description)
            res.append((record.id, name))
        return res
