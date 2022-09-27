from odoo import fields, models


class ProductUom(models.Model):
    _inherit = "uom.uom"

    # l10n_co_edi_ubl = fields.Char(string=u'Código UBL')
    l10n_co_edi_country_code = fields.Char(default=lambda self: self.env.company.country_id.code)
    l10n_co_edi_ubl_id = fields.Many2one("l10n_co_edi.uom.code", string="Código UBL")

    unspsc_code_id = fields.Many2one(
        "product.unspsc.code",
        "UNSPSC Product Category",
        domain=[("applies_to", "=", "uom")],
        help="The UNSPSC code related to this UoM. ",
    )
