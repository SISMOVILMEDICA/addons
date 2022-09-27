from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # l10n_co_edi_large_taxpayer = fields.Boolean(string='Gran Contribuyente')

    l10n_co_edi_representation_type_id = fields.Many2one(
        "l10n_co_edi.type_code",
        string="Tipo de Representación",
        domain=[("type", "=", "representation")],
    )
    l10n_co_edi_establishment_type_id = fields.Many2one(
        "l10n_co_edi.type_code",
        string="Tipo Establecimiento",
        domain=[("type", "=", "establishment")],
    )

    l10n_co_edi_obligation_type_ids = fields.Many2many(
        "l10n_co_edi.type_code",
        "partner_l10n_co_edi_obligation_types",
        "partner_id",
        "type_id",
        string="Obligaciones y Responsabilidades",
        domain=[("type", "=", "obligation"), ("is_required_dian", "=", True)],
    )
    l10n_co_edi_customs_type_ids = fields.Many2many(
        "l10n_co_edi.type_code",
        "partner_l10n_co_edi_customs_types",
        "partner_id",
        "type_id",
        string="Usuario Aduanero",
        domain=[("type", "=", "customs")],
    )
    # l10n_co_edi_simplified_regimen = fields.Boolean('Simplified Regimen')
    l10n_co_edi_fiscal_regimen = fields.Selection(
        [
            ("48", "Responsable del Impuesto sobre las ventas - IVA"),
            ("49", "No responsables del IVA"),
        ],
        string="Fiscal Regimen",
        required=True,
        default="48",
    )
    l10n_co_edi_tax_scheme_id = fields.Many2one(
        "l10n_co_edi.tax.type", string="Responsabilidad Tributaria"
    )

    l10n_co_edi_commercial_name = fields.Char("Commercial Name")

    # vat_dv = fields.Char(string="DV", default="")
    l10n_co_verification_code = fields.Char(
        compute="_compute_verification_code",
        string="VC",
        help="Redundancy check to verify the vat number has been typed in correctly.",
    )
    edi_email = fields.Char(string="Correo EDI", help="Correo para facturación electrónica.")

    @api.depends("vat", "l10n_latam_identification_type_id")
    def _compute_verification_code(self):
        multiplication_factors = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]

        for partner in self:
            if partner.l10n_latam_identification_type_id.l10n_co_edi_code == "31":
                if (
                    partner.vat
                    and partner.country_id == self.env.ref("base.co")
                    and len(partner.vat) <= len(multiplication_factors)
                ):
                    number = 0
                    padded_vat = partner.vat

                    while len(padded_vat) < len(multiplication_factors):
                        padded_vat = "0" + padded_vat

                    # if there is a single non-integer in vat the verification code should be False
                    try:
                        for index, vat_number in enumerate(padded_vat):
                            number += int(vat_number) * multiplication_factors[index]

                        number %= 11

                        if number < 2:
                            partner.l10n_co_verification_code = number
                        else:
                            partner.l10n_co_verification_code = 11 - number
                    except ValueError:
                        partner.l10n_co_verification_code = False
                else:
                    partner.l10n_co_verification_code = False
            else:
                partner.l10n_co_verification_code = False

    def _get_vat_without_verification_code(self):
        self.ensure_one()
        # last digit is the verification code
        # last digit is the verification code, but it could have a - before
        if (
            self.l10n_latam_identification_type_id.l10n_co_document_code != "rut"
            or self.vat == "222222222222"
        ):
            return self.vat
        elif self.vat and "-" in self.vat:
            return self.vat.split("-")[0]
        return self.vat[:-1] if self.vat else ""

    def _get_vat_verification_code(self):
        self.ensure_one()
        if self.l10n_latam_identification_type_id.l10n_co_document_code != "rut":
            return ""
        elif self.vat and "-" in self.vat:
            return self.vat.split("-")[1]
        return self.vat[-1] if self.vat else ""

    def _l10n_co_edi_get_fiscal_values(self):
        return self.l10n_co_edi_obligation_type_ids | self.l10n_co_edi_customs_type_ids

    # @api.multi
    def check_vat_co(self, vat):
        return True

    @api.constrains("vat", "country_id")
    def check_vat(self):
        if self.sudo().env.ref("base.module_base_vat").state == "installed":
            self = self.filtered(lambda partner: partner.country_id != self.env.ref("base.co"))
            return super(ResPartner, self).check_vat()
        else:
            return True

    def _l10n_co_edi_get_carvajal_code_for_identification_type(self, partner):
        IDENTIFICATION_TYPE_TO_CARVAJAL_CODE = {
            "rut": "31",
            "id_card": "12",
            "national_citizen_id": "13",
            "id_document": "12",
            "passport": "41",
            "external_id": "21",
            "foreign_id_card": "22",
            "diplomatic_card": "O-99",
            "residence_document": "O-99",
            "civil_registration": "11",
        }

        identification_type = partner.l10n_latam_identification_type_id.l10n_co_document_code
        return (
            IDENTIFICATION_TYPE_TO_CARVAJAL_CODE[identification_type] if identification_type else ""
        )

    def _l10n_co_edi_get_partner_type(self):
        self.ensure_one()
        if self.is_company:
            return "1"  # '3' if self.l10n_co_edi_large_taxpayer else
        else:
            return "2"

    # ****************************************

    def _get_address_partner_edi(self):
        if self.country_id and self.country_id.code == "CO":
            if not self.city_id:
                raise UserError(_("%s no tiene una ciudad establecida.") % self.name)
            elif not self.state_id:
                raise UserError(_("%s no tiene una departamento establecido.") % self.name)
        else:
            raise UserError(_("%s no tiene una país establecido.") % self.name)

        return {
            "AddressID": self.city_id.l10n_co_edi_code or "",
            "AddressCityName": self.city_id.name or "",
            "AddressPostalZone": self.zip or self.city_id.zipcode or "",
            "AddressCountrySubentity": self.state_id.name or "",
            "AddressCountrySubentityCode": self.state_id.l10n_co_edi_code or "",
            "AddressLine": self.street or "",
            "CountryIdentificationCode": self.country_id.code,
            "CountryName": self.country_id.name,
        }

    def _get_accounting_partner_party_edi(self):
        self.ensure_one()
        person_type = self._l10n_co_edi_get_partner_type()

        # Ubicaciones
        if self.country_id:
            if self.country_id.code == "CO" and not self.city_id:
                raise UserError(_("%s no tiene una ciudad establecida.") % self.name)
            elif self.country_id.code == "CO" and not self.state_id:
                raise UserError(_("%s no tiene un departamento establecido.") % self.name)
        else:
            raise UserError(_("%s no tiene un país establecido.") % self.name)

        # Identificación
        if self.l10n_latam_identification_type_id:
            document_type_code = self.l10n_latam_identification_type_id.l10n_co_edi_code
            if not document_type_code:
                raise UserError(
                    _("El tipo de documento [%s] no tiene código DIAN. \n" "En el contacto %s")
                    % (self.l10n_latam_identification_type_id.name, self.name)
                )
            if document_type_code == "31" and not self.l10n_co_verification_code:
                raise ValidationError(_("%s no tiene dígito de verificación.") % self.name)
            if not self.vat:
                raise ValidationError(_("%s no tiene número de identificación.") % self.name)
        else:
            raise UserError(
                _("%s no tiene un tipo de documento de identificación establecido.") % self.name
            )

        if (
            not self.l10n_co_edi_obligation_type_ids
            or not self.l10n_co_edi_tax_scheme_id
            or not self.l10n_co_edi_fiscal_regimen
        ):
            raise UserError(
                _(
                    "%s no tiene su información fiscal correctamente configurada. \n"
                    "Por favor, configurela desde Contactos"
                )
                % self.name
            )

        tax_level_codes = ""
        for tax_level_code_id in self.l10n_co_edi_obligation_type_ids:
            if tax_level_codes == "":
                tax_level_codes = tax_level_code_id.name
            else:
                tax_level_codes += ";" + tax_level_code_id.name

        telephone = False
        if self.phone and self.mobile:
            telephone = self.phone + " / " + self.mobile
        elif self.phone:
            telephone = self.phone
        elif self.mobile:
            telephone = self.mobile

        return {
            "AdditionalAccountID": person_type,
            "PartyName": self.l10n_co_edi_commercial_name or self.name,  # se podria comentar
            "Name": self.name,
            "AddressID": self.city_id.l10n_co_edi_code or "",
            "AddressCityName": self.city_id.name or "",
            "AddressPostalZone": self.zip or self.city_id.zipcode or "",
            "AddressCountrySubentity": self.state_id.name or "",
            "AddressCountrySubentityCode": self.state_id.l10n_co_edi_code or "",
            "AddressLine": self.street or "",
            "CompanyIDschemeID": self.l10n_co_verification_code,
            "CompanyIDschemeName": self.l10n_latam_identification_type_id.l10n_co_edi_code,
            "CompanyID": self.vat,
            "listName": self.l10n_co_edi_fiscal_regimen,
            "TaxLevelCode": tax_level_codes,
            "TaxSchemeID": self.l10n_co_edi_tax_scheme_id.code,
            "TaxSchemeName": self.l10n_co_edi_tax_scheme_id.name,
            "CorporateRegistrationSchemeName": self.ref,
            "CountryIdentificationCode": self.country_id.code,
            "CountryName": self.country_id.name,
            "Telephone": telephone,
            "Telefax": "",
            "ElectronicMail": self.email,
        }

    def _get_tax_representative_party_values(self):
        if not self.l10n_latam_identification_type_id:
            raise ValidationError(_("%s no tiene tipo de identificación.") % self.name)
        if not self.vat:
            raise ValidationError(_("%s no tiene número de identificación.") % self.name)
        if (
            self.l10n_latam_identification_type_id.l10n_co_edi_code == "31"
            and not self.l10n_co_verification_code
        ):
            raise ValidationError(_("%s no tiene dígito de verificación.") % self.name)

        return {
            "ID": self.vat,
            "IDschemeID": self.l10n_co_verification_code,
            "IDschemeName": self.l10n_latam_identification_type_id.l10n_co_edi_code,
        }
