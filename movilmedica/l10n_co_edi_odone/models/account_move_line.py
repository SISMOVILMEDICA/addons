from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _l10n_co_edi_get_product_code(self):
        """
        For identifying products, different standards can be used.  If there is a barcode, we take that one, because
        normally in the GTIN standard it will be the most specific one.  Otherwise, we will check the
        :return: (standard, product_code)
        """
        self.ensure_one()
        code = []
        if self.product_id:
            if self.move_id.l10n_co_edi_type == "2":
                if not self.product_id.l10n_co_edi_customs_code:
                    raise UserError(
                        _(
                            "Las facturas de exportación requieren un código aduanero en todos los productos, "
                            "complete esta información antes de validar la factura."
                        )
                    )
                code = [self.product_id.l10n_co_edi_customs_code, "020", "195"]
            if self.product_id.barcode:
                code = [self.product_id.barcode, "010", "9"]
            elif self.product_id.unspsc_code_id:
                code = [self.product_id.unspsc_code_id.code, "001", "10"]
            elif self.product_id.default_code:
                code = [self.product_id.default_code, "999", ""]
        if not code:
            code = ["NA", "999", ""]
        return {"ID": code[0], "schemeID": code[1], "schemeAgencyID": code[2]}

    def _get_information_content_provider_party_values(self):
        return {"IDschemeID": False, "IDschemeName": False, "ID": False}

    def _get_taxes_line_edi(self, dict_tax, tax, rate, type_tax):
        tax_code = tax.l10n_co_edi_type.code
        tax_name = tax.l10n_co_edi_type.name
        tax_amount = tax.amount
        tax_percent = "{:.2f}".format(float(tax_amount))

        if tax_code not in dict_tax:
            dict_tax[tax_code] = {}
            dict_tax[tax_code]["total"] = 0
            dict_tax[tax_code]["name"] = tax_name
            dict_tax[tax_code]["taxes"] = {}

        if tax_percent not in dict_tax[tax_code]["taxes"]:
            dict_tax[tax_code]["taxes"][tax_percent] = {}
            dict_tax[tax_code]["taxes"][tax_percent]["base"] = 0
            dict_tax[tax_code]["taxes"][tax_percent]["amount"] = 0

        if type_tax == "header":
            dict_tax[tax_code]["total"] += (
                (self.tax_base_amount / rate) * self.tax_line_id.amount
            ) / 100
            dict_tax[tax_code]["taxes"][tax_percent]["base"] += self.tax_base_amount / rate
            dict_tax[tax_code]["taxes"][tax_percent]["amount"] += (
                (self.tax_base_amount / rate) * self.tax_line_id.amount
            ) / 100
        if type_tax == "item":
            dict_tax[tax_code]["total"] += self.price_subtotal * tax_amount / 100
            dict_tax[tax_code]["taxes"][tax_percent]["base"] += self.price_subtotal
            dict_tax[tax_code]["taxes"][tax_percent]["amount"] += (
                self.price_subtotal * tax_amount / 100
            )

        return dict_tax
