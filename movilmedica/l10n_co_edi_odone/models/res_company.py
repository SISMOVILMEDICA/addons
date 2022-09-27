from lxml import etree
from requests import exceptions, post

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import l10n_co_edi_sentences


class ResCompany(models.Model):
    _inherit = "res.company"

    type_einvoicing = fields.Selection(
        [
            ("no", "No Aplica"),
            ("edi_dir", "Directa a la DIAN"),
        ],
        string="Facturación Electrónica",
        default="no",
    )

    fv_sent = fields.Integer(string="Facturas")
    nc_sent = fields.Integer(string="Notas Crédito")
    nd_sent = fields.Integer(string="Notas Débito")
    zip_sent = fields.Integer(string="Zips")

    profile_execution_id = fields.Selection(
        [("1", "Producción"), ("2", "Test")], "Ambiente de destino", default="2", required=True
    )
    test_set_id = fields.Char(string="Test Set Id")
    software_id = fields.Char(string="Software Id")
    software_pin = fields.Char(string="Software PIN")
    certificate_filename = fields.Char(string="Nombre Certificado")
    certificate_file = fields.Binary(string="Certificado")
    certificate_password = fields.Char(string="Pwd Certificado")
    signature_policy_url = fields.Char(
        string="Url Politica de firma",
        default="https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf",
    )
    signature_policy_description = fields.Char(
        string="Descripción Política de firma",
        default="Política de firma para facturas electrónicas de la República de Colombia.",
    )
    signature_policy_filename = fields.Char(string="Nombre Archivo política de firma")
    signature_policy_file = fields.Binary(string="Archivo política de firma")
    response_get_numbering_range = fields.Text(string="Respuesta Rangos de Numeración")
    tributary_information = fields.Text(string="Información Tributaria")

    edi_email = fields.Char(
        string="Correos de facturación electrónica",
        help="Correo de origen para facturación electrónica",
    )
    edi_email_error = fields.Char(
        string="Correos para notificación de errores",
        help="Para agregar varios correos, se debe separar con una coma (,).",
    )
    report_template = fields.Many2one(string="Report Template", comodel_name="ir.actions.report")

    def action_GetNumberingRange(self):
        msg1 = _("Error desconocido,\nCódigo de estado: %s,\nRazón: %s.")
        msg2 = _("Error desconocido: %s\n.")
        wsdl = "https://vpfe.dian.gov.co/WcfDianCustomerServices.svc?wsdl"
        s = "http://www.w3.org/2003/05/soap-envelope"
        b = "http://wcf.dian.colombia"

        GetNumberingRange_values = self._get_GetNumberingRange_values()
        GetNumberingRange_values["To"] = wsdl.replace("?wsdl", "")
        xml_soap_with_signature = l10n_co_edi_sentences.get_xml_soap_with_signature(
            l10n_co_edi_sentences.render_xml_edi(GetNumberingRange_values, "GetNumberingRange"),
            GetNumberingRange_values["Id"],
            self.certificate_file,
            self.certificate_password,
        )
        try:
            response = post(
                wsdl,
                headers={"content-type": "application/soap+xml;charset=utf-8"},
                data=etree.tostring(xml_soap_with_signature),
            )

            if response.status_code == 200:
                root = etree.fromstring(response.text)
                response = ""

                for element in root.iter("{%s}Body" % s):
                    response = etree.tostring(element, pretty_print=True)
                    for element in root.iter("{%s}GetNumberingRangeResult" % b):
                        response = etree.tostring(element, pretty_print=True, encoding="utf-8")
                if response == "":
                    response = etree.tostring(root, pretty_print=True)

                self.write({"response_get_numbering_range": response})
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))

        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

        return True

    def _get_GetNumberingRange_values(self):
        xml_soap_values = l10n_co_edi_sentences.get_xml_soap_values(
            self.certificate_file, self.certificate_password
        )
        xml_soap_values["accountCode"] = self.partner_id.vat
        xml_soap_values["accountCodeT"] = self.partner_id.vat
        xml_soap_values["softwareCode"] = self.software_id

        return xml_soap_values
