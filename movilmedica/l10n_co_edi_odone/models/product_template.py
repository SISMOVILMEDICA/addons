from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_co_edi_brand = fields.Char(
        string="Marca", help="Marca reportada en la factura electrónica colombiana."
    )
    l10n_co_edi_model = fields.Char(
        string="Modelo", help="Modelo reportado en la factura electrónica colombiana."
    )
    l10n_co_edi_customs_code = fields.Char(
        string="Código Aduanero", help="Necesario principalmente para facturas de exportación."
    )

    unspsc_code_id = fields.Many2one(
        "product.unspsc.code",
        "Categoría de producto UNSPSC",
        domain=[("applies_to", "=", "product")],
        help="El código UNSPSC relacionado con este producto. Utilizado para edi en Colombia, Perú y México",
    )
