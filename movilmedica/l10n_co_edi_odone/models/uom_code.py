from odoo import fields, models


class UomCode(models.Model):
    _name = "l10n_co_edi.uom.code"
    _description = "Tipo de unidad de medida paa la DIAN"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")

    def name_get(self):
        res = []
        for record in self:
            name = "[{}] {}".format(record.code or "", record.name)
            res.append((record.id, name))
        return res
