from odoo import api, fields, models


class IdentificationType(models.Model):
    _inherit = "l10n_latam.identification.type"

    l10n_co_edi_code = fields.Char(string="Código EDI")

    def name_get(self):
        res = []
        for record in self:
            name = "[{}] {}".format(record.l10n_co_edi_code or "", record.name)
            res.append((record.id, name))
        return res
