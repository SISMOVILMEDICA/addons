import logging
import re
from base64 import b64decode, b64encode
from datetime import datetime
from io import BytesIO
from zipfile import ZIP_BZIP2, ZipFile

from lxml import etree
from pytz import timezone
from requests import exceptions, post

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang, get_lang

from . import l10n_co_edi_sentences

_logger = logging.getLogger(__name__)

DIAN = {
    "wsdl-hab": "https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl",
    "wsdl": "https://vpfe.dian.gov.co/WcfDianCustomerServices.svc?wsdl",
    "catalogo-hab": "https://catalogo-vpfe-hab.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}",
    "catalogo": "https://catalogo-vpfe.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}",
}

EDI_OPERATION_TYPE = [
    ("10", "Estandar"),
    ("09", "AIU"),
    ("11", "Mandatos"),
    ("20", "Nota Crédito que referencia una factura electrónica"),
    ("22", "Nota Crédito sin referencia a facturas"),
    # ('23', 'Nota Crédito para facturación electrónica V1 (Decreto 2242)'),
    ("30", "Nota Débito que referencia una factura electrónica"),
    ("32", "Nota Débito sin referencia a facturas"),
    # ('33', 'Nota Débito para facturación electrónica V1 (Decreto 2242)')
]


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_einv_warning(self):
        warn_remaining = False
        inactive_resolution = False

        if self.journal_id.sequence_id.edi_resolution_control:
            remaining_numbers = self.journal_id.remaining_numbers
            remaining_days = self.journal_id.remaining_days
            date_range = self.env["ir.sequence.date_range"].search(
                [
                    ("sequence_id", "=", self.journal_id.sequence_id.id),
                    ("active_resolution", "=", True),
                ]
            )
            today = datetime.strptime(str(fields.Date.today(self)), "%Y-%m-%d")
            if date_range:
                date_range.ensure_one()
                date_to = datetime.strptime(str(date_range.date_to), "%Y-%m-%d")
                days = (date_to - today).days
                numbers = date_range.number_to - date_range.number_next_actual
                if numbers < remaining_numbers or days < remaining_days:
                    warn_remaining = True
            else:
                inactive_resolution = True
        self.is_inactive_resolution = inactive_resolution
        self.l10n_co_edi_warning = warn_remaining

    l10n_co_edi_warning = fields.Boolean(
        string="Advertir por rangos reolucióm?", compute="_get_einv_warning", store=False
    )
    is_inactive_resolution = fields.Boolean(
        string="Advertir Resolución Inactiva?", compute="_get_einv_warning", store=False
    )

    l10n_co_edi_invoice_name = fields.Char(
        "Factura Electrónica",
        help="Consecutivo de la factura electrónica publicada en la DIAN.",
        readonly=True,
        copy=False,
    )
    l10n_co_edi_datetime_invoice = fields.Datetime(
        string="Fecha Validación",
        help="Campo técnico utilizado para almacenar la hora de validación de la factura.",
        copy=False,
    )
    l10n_co_edi_type = fields.Selection(
        [
            ("01", "Factura de venta"),
            ("02", "Factura de exportación"),
            ("03", "Documento electrónico de transmisión – tipo 03"),
            ("04", "Factura electrónica de Venta - tipo 04"),
        ],
        required=True,
        default="01",
        string="Tipo de Factura Electrónica",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    l10n_co_edi_operation_type = fields.Selection(
        EDI_OPERATION_TYPE, string="Operation Type", default="10", required=True
    )
    l10n_co_edi_payment_option_id = fields.Many2one(
        "l10n_co_edi.payment.option",
        string="Payment Option",
        default=lambda self: self.env.ref(
            "l10n_co_edi_odone.payment_option_1", raise_if_not_found=False
        ),
    )
    l10n_co_edi_is_direct_payment = fields.Boolean(
        "Direct Payment from Colombia", compute="_compute_l10n_co_edi_is_direct_payment"
    )
    l10n_co_edi_mandante_id = fields.Many2one("res.partner", string="Mandante")

    edi_cufe_cude_ref = fields.Char(string="CUFE/CUDE", readonly=True, copy=False)
    edi_url = fields.Char("Url", copy=False)
    edi_unencoded_cufe_cude = fields.Char(string="CUFE/CUDE sin codificar", copy=False)
    edi_unencoded_soft_security_code = fields.Char(
        string="Código de seguridad del software sin codificar", copy=False
    )
    edi_soft_security_code = fields.Char(string="Código de seguridad del software", copy=False)
    edi_qr_image = fields.Binary("Código QR", compute="_compute_edi_qr_code")

    is_external_invoice = fields.Boolean("Factura externa?", copy=False)
    name_invoice_reference = fields.Char("Número Factura", copy=False)
    uuid_invoice_reference = fields.Char("Cufe", copy=False)
    issue_date_invoice_reference = fields.Date("Fecha", copy=False)
    operation_type_invoice_reference = fields.Selection(
        EDI_OPERATION_TYPE[:3], string="Tipo operación"
    )

    l10n_co_edi_discrepancy_response_id = fields.Many2one(
        "l10n_co_edi.discrepancy.response", string="Concepto de corrección"
    )
    type_note = fields.Selection(
        [("debit", "Nota Débito"), ("credit", "Nota Crédito")], string="Tipo de Nota"
    )
    credit_note_ids = fields.One2many(
        "account.move", "reversed_entry_id", string="Notas crédito", copy=False
    )
    credit_note_count = fields.Integer("Número de notas crédito", compute="_compute_credit_count")

    # DIAN DOC
    is_einvoicing_journal = fields.Boolean(
        string="Diario con facturación electrónica", related="journal_id.is_einvoicing"
    )

    edi_pdf_filename = fields.Char(string="Nombre Pdf", copy=False)
    edi_pdf_file = fields.Binary(string="Archivo Pdf", copy=False)
    edi_xml_filename = fields.Char(string="Nombre XML", copy=False)
    edi_xml_file = fields.Binary(string="Archivo XML", copy=False)
    edi_attachment_filename = fields.Char(
        string="Nombre Attachment", copy=False, default="Attachment.xml"
    )
    edi_attachment_file = fields.Binary(string="Archivo Attachment", copy=False)
    edi_zipped_filename = fields.Char(string="Nombre Zip", copy=False)
    edi_zipped_file = fields.Binary(string="Archivo Zip", copy=False)
    edi_ar_filename = fields.Char(
        string="ApplicationResponse XML Filename", copy=False, default="ApplicationResponse.xml"
    )  # ar_xml_filename
    edi_ar_file = fields.Binary(string="ApplicationResponse XML File", copy=False)  # ar_xml_file
    edi_zip_key = fields.Char(string="ZipKey", copy=False)

    # Response
    l10n_co_edi_state = fields.Selection(
        [
            ("00", "Procesado Correctamente"),
            ("66", "NSU no encontrado"),
            ("90", "TrackId no encontrado"),
            ("99", "Validaciones contienen errores en campos mandatorios"),
            ("other", "Other"),
        ],
        string="Estado Doc.",
        default=False,
        copy=False,
    )
    l10n_co_edi_response = fields.Text(string="Respuesta", copy=False)
    mail_sent = fields.Boolean(string="Correo enviado?", copy=False)

    def _compute_edi_qr_code(self):
        qr_data = "NA"
        if self.is_einvoicing_journal:
            edi_taxes = self._get_einvoicing_taxes()
            ValImp1 = edi_taxes["TaxesTotal"]["01"]["total"]
            ValImp2 = edi_taxes["TaxesTotal"]["04"]["total"]
            ValImp3 = edi_taxes["TaxesTotal"]["03"]["total"]
            ValFac = self.amount_untaxed
            ValOtroIm = ValImp2 - ValImp3
            ValTolFac = ValFac + ValImp1 + ValImp2 + ValImp3
            date_format = str(self.create_date)[0:19]
            create_date = datetime.strptime(date_format, "%Y-%m-%d %H:%M:%S")
            create_date = create_date.replace(tzinfo=timezone("UTC"))
            nit_fac = self.company_id.partner_id.vat
            nit_adq = self.partner_id.vat
            cufe = self.edi_cufe_cude_ref
            number = self.name  # l10n_co_edi_invoice_name

            qr_data = "NumFac: " + number if number and number != "/" else "NO_VALIDADA"

            qr_data += "\nNitFac: " + nit_fac if nit_fac else ""
            qr_data += "\nNitAdq: " + nit_adq if nit_adq else ""
            qr_data += "\nValFac: " + "{:.2f}".format(ValFac)
            qr_data += "\nValIva: " + "{:.2f}".format(ValImp1)
            qr_data += "\nValOtroIm: " + "{:.2f}".format(ValOtroIm)
            qr_data += "\nValTolFac: " + "{:.2f}".format(ValTolFac)
            qr_data += "\nCUFE: " + cufe if cufe else ""
            qr_data += "\n\n" + self.edi_url if self.edi_url else ""

        self.edi_qr_image = l10n_co_edi_sentences.get_qr_code(qr_data)

    @api.depends("invoice_date_due", "date")
    def _compute_l10n_co_edi_is_direct_payment(self):
        for rec in self:
            rec.l10n_co_edi_is_direct_payment = (
                rec.date == rec.invoice_date_due
            ) and rec.company_id.country_id.code == "CO"

    @api.depends("credit_note_ids")
    def _compute_credit_count(self):
        credit_data = self.env["account.move"].read_group(
            [("reversed_entry_id", "in", self.ids)], ["reversed_entry_id"], ["reversed_entry_id"]
        )
        data_map = {
            datum["reversed_entry_id"][0]: datum["reversed_entry_id_count"] for datum in credit_data
        }
        for inv in self:
            inv.credit_note_count = data_map.get(inv.id, 0.0)

    def action_view_credit_notes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Notas Crédito"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("reversed_entry_id", "=", self.id)],
        }

    def _get_sequence(self):
        """Return the sequence to be used during the post of the current move.
        :return: An ir.sequence record or False.
        """
        res = super(AccountMove, self)._get_sequence()

        journal = self.journal_id
        if self.move_type == "out_invoice" and not self.type_note:
            return journal.sequence_id
        elif self.move_type == "out_refund" and self.type_note == "credit":
            return journal.refund_sequence_id
        elif self.move_type == "out_invoice" and self.type_note == "debit":
            return journal.debit_note_sequence_id
        return res

    def _post(self, soft=True):
        for record in self:
            if record.state != "draft":
                raise ValidationError(
                    _(
                        "La factura [id: %s] no se encuentra en estado borrador y no se puede publicar. \n"
                        "Por favor, refresque la página para actualizar la información."
                    )
                    % record.id
                )
        res = super(AccountMove, self)._post(soft)
        for record in self:
            if (
                record.move_type in ("out_invoice", "out_refund")
                and record.company_id.type_einvoicing == "edi_dir"
                and record.journal_id.is_einvoicing
            ):
                if record.name and record.name != "/":
                    record.l10n_co_edi_invoice_name = record.name
                    # # Get the journal's sequence.
                    # sequence = record._get_edi_sequence()
                    # if not sequence:
                    #     raise UserError(_('Por favor defina las secuencias de facturación electrónica en el diario.'))
                    # # Consume a new number.
                    # record.l10n_co_edi_invoice_name = sequence.with_context(ir_sequence_date=record.date).next_by_id()

                record.get_xml_edi_files()
                #  PARA ENVIAR Y CONSULTAR ESTADO DIAN
                if len(self) == 1:
                    # if self.send_invoice_to_dian == '0':
                    if record.l10n_co_edi_type in ("01", "02", "03"):
                        record.action_sent_zipped_file()
                    elif record.invoice_type_code == "04":
                        record.action_send_mail()
                #     message = {
                #         'type': 'ir.actions.client',
                #         'tag': 'display_notification',
                #         'params': {
                #             'title': _('Warning!'),
                #             'message': 'Publicando una sola factura',
                #             'sticky': False,}
                #         }
                #     return message

        return res

    def get_xml_edi_files(self):
        self.ensure_one()
        if not self.edi_xml_filename or not self.edi_zipped_filename or not self.edi_pdf_filename:
            self._get_edi_filenames()
        self.edi_xml_file = b64encode(self._get_xml_edi_file()).decode("utf-8", "ignore")
        # self.edi_pdf_file = b64encode(self._get_pdf_file()).decode("utf-8", "ignore")
        # self.edi_pdf_file = self._get_pdf_file()
        self.edi_zipped_file = b64encode(self._get_zipped_file(with_pdf=False)).decode(
            "utf-8", "ignore"
        )

    def action_invoice_sent(self):
        """Open a window to compose an email, with the edi invoice template
        message loaded by default
        """
        self.ensure_one()
        if self.is_einvoicing_journal:
            template = self.env.ref(
                "l10n_co_edi_odone.l10n_co_edi_email_template", raise_if_not_found=False
            )
        else:
            template = self.env.ref("account.email_template_edi_invoice", raise_if_not_found=False)

        attach_ids = []
        zip_attachment_file = False
        if self.edi_zipped_file:
            zip_attachment_file = self.env["ir.attachment"].create(
                {
                    "name": self.edi_zipped_filename,
                    "type": "binary",
                    "datas": self.edi_zipped_file,
                }
            )

        if zip_attachment_file:
            attach_ids.append(zip_attachment_file.id)
        if attach_ids:
            template.attachment_ids = [(6, 0, attach_ids)]

        lang = False
        if template:
            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        compose_form = self.env.ref(
            "account.account_invoice_send_wizard_form", raise_if_not_found=False
        )
        ctx = dict(
            default_model="account.move",
            default_res_id=self.id,
            # For the sake of consistency we need a default_res_model if
            # default_res_id is set. Not renaming default_model as it can
            # create many side-effects.
            default_res_model="account.move",
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).type_name,
            force_email=True,
        )

        return {
            "name": _("Send Invoice"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.invoice.send",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    def _get_type_document(self):
        self.ensure_one()

        if self.move_type == "out_invoice" and not self.type_note:
            return "invoice"
        elif self.move_type == "out_refund" and self.type_note != "debit":
            return "credit"
        elif self.move_type == "out_invoice" and self.type_note == "debit":
            return "debit"
        else:
            return False

    def _get_edi_filenames(self):
        self.ensure_one()
        name_pdf = ""
        # nnnnnnnnnn: NIT del Facturador Electrónico sin DV, de diez (10) dígitos alineados a la derecha y relleno con ceros a la izquierda.
        nnnnnnnnnn = ""
        # Código ppp es 000 para Software Propio
        ppp = "000"
        # aa: Dos (2) últimos dígitos año calendario
        aa = ""
        # dddddddd: consecutivo de archivos enviados, de ocho (8) dígitos decimales alineados a la derecha
        # y ajustado a la izquierda con ceros, en el rango: 00000001 <= 99999999
        # Cada Año, el 1ro de enero se debe reiniciar en consecutivo de archivos enviados “dddddddd” a 00000001.
        dddddddd = ""

        if self.company_id.partner_id.vat:
            nnnnnnnnnn = self.company_id.partner_id.vat.zfill(10)
        else:
            raise ValidationError(
                "El documento de identificación de %s no está establecido. \n"
                % self.company_id.partner_id.name
            )

        aa = datetime.now().replace(tzinfo=timezone(self.env.user.tz)).strftime("%y")

        fv_sent = self.company_id.fv_sent
        nc_sent = self.company_id.nc_sent
        nd_sent = self.company_id.nd_sent
        zip_sent = self.company_id.zip_sent
        # fv_sent + nc_sent + nd_sent
        type_document = self._get_type_document()
        if type_document == "invoice":
            xml_filename_prefix = "fv"
            dddddddd = str(fv_sent + 1).zfill(8)
            name_pdf = _("Factura")
        elif type_document == "credit":
            xml_filename_prefix = "nc"
            dddddddd = str(nc_sent + 1).zfill(8)
            name_pdf = _("Nota Crédito")
        elif type_document == "debit":
            xml_filename_prefix = "nd"
            dddddddd = str(nd_sent + 1).zfill(8)
            name_pdf = _("Nota Débito")
        else:
            raise ValidationError(
                "ERROR: No se puede definir el tipo de documento electrónico de este asiento"
            )

        # Falta
        # arnnnnnnnnnnpppaadddddddd.xml
        # adnnnnnnnnnnpppaadddddddd.xml

        zdddddddd = str(zip_sent + 1).zfill(8)
        nnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + dddddddd
        znnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + zdddddddd

        self.write(
            {
                "edi_xml_filename": xml_filename_prefix + nnnnnnnnnnpppaadddddddd + ".xml",
                "edi_zipped_filename": "z" + znnnnnnnnnnpppaadddddddd + ".zip",
                "edi_pdf_filename": "{} {}.pdf".format(name_pdf, self.name),
            }
        )

    def get_name_type_document(self):
        self.ensure_one()
        type_document = self._get_type_document()
        name_doc = ""
        if type_document == "invoice":
            name_doc = _("Factura")
        elif type_document == "credit":
            name_doc = _("Nota Crédito")
        elif type_document == "debit":
            name_doc = _("Nota Débito")

        return name_doc

    def _get_xml_edi_file(self):
        self.ensure_one()
        type_document = self._get_type_document()
        if type_document == "invoice":
            doc_values = self._get_values_fv_edi()
            doc_template = "Invoice"
        elif type_document == "credit":
            doc_values = self._get_values_nc_edi()
            doc_template = "CreditNote"
            # unsigned_xml = l10n_co_edi_sentences.get_template_xml(self._get_credit_note_values(), 'CreditNote')
        elif type_document == "debit":
            doc_values = self._get_values_nd_edi()
            doc_template = "DebitNote"
            # unsigned_xml = l10n_co_edi_sentences.get_template_xml(self._get_debit_note_values(), 'DebitNote')
        else:
            raise ValidationError(
                "ERROR: No se puede definir el tipo de documento electrónico de este asiento"
            )

        unsigned_xml = l10n_co_edi_sentences.render_xml_edi(doc_values, doc_template)

        xml_with_signature = l10n_co_edi_sentences.get_xml_with_signature(
            unsigned_xml,
            self.company_id.signature_policy_url,
            self.company_id.signature_policy_description,
            self.company_id.certificate_file,
            self.company_id.certificate_password,
        )

        return xml_with_signature

    def _get_values_fv_edi(self):
        self.ensure_one()
        # xml_values = self._get_xml_values(False)
        xml_values = self._get_val_xml_edi()
        xml_values["CustomizationID"] = self.l10n_co_edi_operation_type
        # active_resolution = self._get_active_resolution_edi()
        # xml_values['InvoiceControl'] = active_resolution
        xml_values["InvoiceTypeCode"] = self.l10n_co_edi_type
        xml_values["InvoiceLines"] = self._get_values_lines_edi()  # _get_invoice_lines()

        return xml_values

    def _get_values_nc_edi(self):
        self.ensure_one()
        xml_values = self._get_val_xml_edi()
        if self.l10n_co_edi_operation_type == "10" or self.reversed_entry_id:
            billing_reference = self._get_billing_reference()
        else:
            billing_reference = False

        # 20 Nota Crédito que referencia una factura electrónica.
        # 22 Nota Crédito sin referencia a facturas*.
        # 23 Nota Crédito para facturación electrónica V1 (Decreto 2242).
        if billing_reference:
            xml_values["CustomizationID"] = "20"
            self.l10n_co_edi_operation_type = "20"
        elif self.l10n_co_edi_operation_type == "22":
            xml_values["CustomizationID"] = "22"
            self.l10n_co_edi_operation_type = "22"
            billing_reference = {
                "ID": False,
                "UUID": False,
                "IssueDate": False,
                "CustomizationID": False,
            }
        else:
            xml_values["CustomizationID"] = "20"
            self.l10n_co_edi_operation_type = "20"
            billing_reference = {
                "ID": self.name_invoice_reference,
                "UUID": self.uuid_invoice_reference,
                "IssueDate": self.issue_date_invoice_reference,
                "CustomizationID": self.operation_type_invoice_reference,
            }
        # 91 Nota Crédito
        xml_values["CreditNoteTypeCode"] = "91"
        xml_values["BillingReference"] = billing_reference
        xml_values["DiscrepancyReferenceID"] = billing_reference["ID"]
        xml_values["DiscrepancyResponseCode"] = self.l10n_co_edi_discrepancy_response_id.code
        xml_values["DiscrepancyDescription"] = self.l10n_co_edi_discrepancy_response_id.name
        xml_values["CreditNoteLines"] = self._get_values_lines_edi()  # _get_invoice_lines()
        # ACTUALIZACION V1.8 AGOSTO 2021
        xml_values["Prefix_nc"] = self.get_prefix_doc("nc")
        return xml_values

    def get_prefix_doc(self, type_note="inv"):
        self.ensure_one()
        prefix = ""
        if type_note == "inv":
            prefix = self.journal_id.sequence_id.prefix
        elif type_note == "nc":
            prefix = self.journal_id.refund_sequence_id.prefix
        elif type_note == "nd":
            prefix = self.journal_id.debit_note_sequence_id.prefix
        return prefix

    # def _get_debit_note_values(self):
    def _get_values_nd_edi(self):
        self.ensure_one()
        xml_values = self._get_val_xml_edi()
        if self.l10n_co_edi_operation_type == "10" or self.debit_origin_id:
            billing_reference = self._get_billing_reference()
        else:
            billing_reference = False

        # 30 Nota Débito que referencia una factura electrónica.
        # 32 Nota Débito sin referencia a facturas *.
        # 33 Nota Débito para facturación electrónica V1 (Decreto 2242).
        if billing_reference:
            xml_values["CustomizationID"] = "30"
            self.l10n_co_edi_operation_type = "30"
        elif self.l10n_co_edi_operation_type == "32":
            xml_values["CustomizationID"] = "32"
            self.l10n_co_edi_operation_type = "32"
            billing_reference = {
                "ID": False,
                "UUID": False,
                "IssueDate": False,
                "CustomizationID": False,
            }
        else:
            xml_values["CustomizationID"] = "30"
            self.l10n_co_edi_operation_type = "30"
            billing_reference = {
                "ID": self.name_invoice_reference,
                "UUID": self.uuid_invoice_reference,
                "IssueDate": self.issue_date_invoice_reference,
                "CustomizationID": self.operation_type_invoice_reference,
            }
        # 92 Nota Débito
        # TODO 2.0: DebitNoteTypeCode no existe en DebitNote
        # xml_values['DebitNoteTypeCode'] = '92'
        xml_values["BillingReference"] = billing_reference
        xml_values["DiscrepancyReferenceID"] = billing_reference["ID"]
        xml_values["DiscrepancyResponseCode"] = self.l10n_co_edi_discrepancy_response_id.code
        xml_values["DiscrepancyDescription"] = self.l10n_co_edi_discrepancy_response_id.name
        xml_values["DebitNoteLines"] = self._get_values_lines_edi()  # _get_invoice_lines()

        return xml_values

    def _get_val_xml_edi(self):
        self.ensure_one()
        active_resolution = self._get_active_resolution_edi()
        supplier = self.company_id.partner_id
        customer = self.partner_id
        IdSoftware = self.company_id.software_id
        AcSupplierParty = supplier._get_accounting_partner_party_edi()
        AcCustomerParty = customer._get_accounting_partner_party_edi()
        edi_taxes = self._get_einvoicing_taxes()

        self.l10n_co_edi_datetime_invoice = datetime.now()
        date_format = str(self.create_date)[0:19]
        create_date = datetime.strptime(date_format, "%Y-%m-%d %H:%M:%S")
        create_date = create_date.replace(tzinfo=timezone("UTC"))

        NumFac = self.name
        FecFac = self.invoice_date
        HorFac = create_date.astimezone(timezone("America/Bogota")).strftime("%H:%M:%S-05:00")
        ValFac = self.amount_untaxed
        ValImp1 = edi_taxes["TaxesTotal"]["01"]["total"]
        ValImp2 = edi_taxes["TaxesTotal"]["04"]["total"]
        ValImp3 = edi_taxes["TaxesTotal"]["03"]["total"]
        ValTot = ValFac + ValImp1 + ValImp2 + ValImp3
        NitFE = supplier.vat
        NumAdq = customer.vat
        ClTec_SoftPIN = False
        TipoAmbie = self.company_id.profile_execution_id

        if self.move_type == "out_invoice" and not self.type_note:
            ClTec_SoftPIN = active_resolution["technical_key"]
        else:
            ClTec_SoftPIN = self.company_id.software_pin

        cufe_cude = l10n_co_edi_sentences.get_cufe_cude(
            NumFac,
            FecFac,
            HorFac,
            str("{:.2f}".format(ValFac)),
            "01",
            str("{:.2f}".format(ValImp1)),
            "04",
            str("{:.2f}".format(ValImp2)),
            "03",
            str("{:.2f}".format(ValImp3)),
            str("{:.2f}".format(ValTot)),
            NitFE,
            NumAdq,
            ClTec_SoftPIN,
            TipoAmbie,
        )
        SoftwareSecurityCode = l10n_co_edi_sentences.get_software_security_code(
            IdSoftware, self.company_id.software_pin, NumFac
        )
        if TipoAmbie == "1":
            QRCodeURL = DIAN["catalogo"]
        else:
            QRCodeURL = DIAN["catalogo-hab"]

        partition_key = "co|" + str(FecFac).split("-")[2] + "|" + cufe_cude["CUFE/CUDE"][:2]
        emission_date = str(FecFac).replace("-", "")
        QRCodeURL = QRCodeURL.format(cufe_cude["CUFE/CUDE"], partition_key, emission_date)

        if self.l10n_co_edi_type == "02":
            if not self.invoice_incoterm_id:
                raise UserError(_("Es necesario el Incoterm para esta factura tipo exportación."))
            elif not self.invoice_incoterm_id.name or not self.invoice_incoterm_id.code:
                raise UserError(
                    "Incoterm no está correctamente parametrizado.\n"
                    "id: %s" % self.invoice_incoterm_id.id
                )

        InformationContentProviderParty = False
        if self.l10n_co_edi_operation_type == "11":
            InformationContentProviderParty = (
                self.l10n_co_edi_mandante_id._get_tax_representative_party_values()
            )

        # El valor a pagar puede verse afectado, por anticipos, y descuentos y cargos a nivel de factura
        PayableAmount = ValTot

        self.write(
            {
                "edi_url": QRCodeURL,
                "edi_unencoded_cufe_cude": cufe_cude["CUFE/CUDEUncoded"],
                "edi_cufe_cude_ref": cufe_cude["CUFE/CUDE"],
                "edi_unencoded_soft_security_code": SoftwareSecurityCode[
                    "SoftwareSecurityCodeUncoded"
                ],
                "edi_soft_security_code": SoftwareSecurityCode["SoftwareSecurityCode"],
            }
        )

        return {
            # Resolución
            "InvoiceAuthorization": active_resolution["resolution_number"],
            "StartDate": active_resolution["date_from"],
            "EndDate": active_resolution["date_to"],
            "Prefix": active_resolution["prefix"],
            "From": active_resolution["number_from"],
            "To": active_resolution["number_to"],
            # Proveedor Tecnológico
            "ProviderIDschemeID": supplier.l10n_co_verification_code,
            "ProviderIDschemeName": supplier.l10n_latam_identification_type_id.l10n_co_edi_code,
            "ProviderID": NitFE,
            "NitAdquiriente": NumAdq,
            "SoftwareID": IdSoftware,
            "SoftwareSecurityCode": SoftwareSecurityCode["SoftwareSecurityCode"],
            "QRCodeURL": QRCodeURL,
            "ProfileExecutionID": TipoAmbie,
            "ID": NumFac,
            "UUID": cufe_cude["CUFE/CUDE"],
            "IssueDate": FecFac,
            "IssueTime": HorFac,
            "LineCountNumeric": len(self.invoice_line_ids.filtered(lambda l: not l.display_type)),
            "DocumentCurrencyCode": self.currency_id.name,
            "Delivery": customer._get_address_partner_edi(),  # _get_delivery_values(),
            "DeliveryTerms": {
                "LossRiskResponsibilityCode": self.invoice_incoterm_id.code or "",
                "LossRisk": self.invoice_incoterm_id.name or "",
            },
            "AccountingSupplierParty": AcSupplierParty,
            "AccountingCustomerParty": AcCustomerParty,
            "TaxRepresentativeParty": supplier._get_tax_representative_party_values(),  # TODO: No esta completamente claro los datos de que tercero son
            "PaymentMeansID": self._get_payment_mean_edi(),
            "PaymentMeansCode": self.l10n_co_edi_payment_option_id.code or "10",
            "DueDate": self.invoice_date_due,
            "PaymentExchangeRate": self._get_payment_exchange_rate(),
            "PaymentDueDate": self.invoice_date_due,
            "InformationContentProviderParty": InformationContentProviderParty,
            "TaxesTotal": edi_taxes["TaxesTotal"],
            "WithholdingTaxesTotal": edi_taxes["WithholdingTaxesTotal"],
            "LineExtensionAmount": "{:.2f}".format(ValFac),
            "TaxExclusiveAmount": "{:.2f}".format(ValFac),
            "TaxInclusiveAmount": "{:.2f}".format(ValTot),
            "PayableAmount": "{:.2f}".format(PayableAmount),
        }

    def _get_active_resolution_edi(self):
        resolution_data = {}
        for range_id in self.journal_id.sequence_id.date_range_ids.filtered(
            lambda r: r.active_resolution
        ):
            resolution_data = {
                "prefix": self.journal_id.sequence_id.prefix or "",
                "resolution_number": range_id.edi_resolution,
                "date_from": range_id.date_from,
                "date_to": range_id.date_to,
                "number_from": range_id.number_from,
                "number_to": range_id.number_to,
                "technical_key": self.journal_id.edi_technical_key,
            }
        if not resolution_data:
            raise ValidationError(
                "El diario no tiene una resolución de facturación electrónica activa"
            )
        return resolution_data

    def _get_einvoicing_taxes(self):
        taxes = {}
        withholding_taxes = {}
        # Trm
        rate = 1
        company_currency = self.company_id.currency_id
        date = fields.Date.context_today(self)
        if self.currency_id.id != company_currency.id:
            rate = self.currency_id._convert(rate, company_currency, self.company_id, date)

        for line in self.line_ids.filtered(lambda l: l.tax_line_id):
            if line.tax_line_id.l10n_co_edi_type:

                is_withholding = line.tax_line_id.l10n_co_edi_type.retention

                if is_withholding and line.tax_line_id.amount == 0:
                    raise UserError(
                        _(
                            'El importe de la retención "%s" es igual a cero (0), '
                            "el impuesto de retención debe tener monto diferente a cero (0)."
                        )
                        % line.tax_line_id.name
                    )
                elif is_withholding and line.tax_line_id.amount > 0:
                    withholding_taxes = line._get_taxes_line_edi(
                        withholding_taxes, line.tax_line_id, rate, "header"
                    )
                elif is_withholding and line.tax_line_id.amount < 0:
                    # INFO  Las retenciones se recomienda no enviarlas a la DIAN.
                    #       Solo las positivas que indican una autoretencion.
                    pass
                elif not is_withholding and line.tax_line_id.amount < 0:  # XXX
                    raise UserError(
                        _(
                            'El importe del impuesto "%s" es negativo, los impuestos deben tener un monto mayor o igual a cero (0).'
                        )
                        % line.tax_line_id.name
                    )
                elif not is_withholding and line.tax_line_id.amount > 0:
                    taxes = line._get_taxes_line_edi(taxes, line.tax_line_id, rate, "header")
            else:
                raise UserError(
                    _(
                        'El impuesto "%s", no tiene asignado el tipo fiscal de facturación electrónica.'
                    )
                    % line.tax_line_id.name
                )

        if "01" not in taxes:
            taxes["01"] = {
                "total": 0.0,
                "name": "IVA",
                "taxes": {
                    "0.00": {
                        "base": 0,
                        "amount": 0,
                    }
                },
            }
        elif "0.00" not in taxes["01"]["taxes"]:
            taxes["01"]["taxes"]["0.00"] = {
                "base": 0,
                "amount": 0,
            }

        if "03" not in taxes:
            taxes["03"] = {
                "total": 0.0,
                "name": "ICA",
                "taxes": {
                    "0.00": {
                        "base": 0.0,
                        "amount": 0.0,
                    }
                },
            }
        if "04" not in taxes:
            taxes["04"] = {
                "total": 0.0,
                "name": "INC",
                "taxes": {
                    "0.00": {
                        "base": 0,
                        "amount": 0,
                    }
                },
            }

        return {"TaxesTotal": taxes, "WithholdingTaxesTotal": withholding_taxes}

    def _get_payment_mean_edi(self):
        self.ensure_one()
        if self.invoice_date < self.invoice_date_due:
            return "2"  # Credito
        elif self.invoice_date == self.invoice_date_due:
            return "1"  # Contado
        else:
            raise ValidationError(
                _(
                    "Ocurrió un error!!\n \
                                    La fecha de vencimiento no puede ser menor a la fecha de factura \
                                    o se esta calculando incorrectamente."
                )
            )

    def _get_payment_exchange_rate(self):
        company_currency = self.company_id.currency_id
        rate = 1
        # date = self._get_currency_rate_date() or fields.Date.context_today(self)
        date = fields.Date.context_today(self)
        if self.currency_id.id != company_currency.id:
            rate = self.currency_id._convert(rate, company_currency, self.company_id, date)
        return {
            "SourceCurrencyCode": self.currency_id.name,
            "TargetCurrencyCode": company_currency.name,
            "CalculationRate": rate,
            "Date": date,
        }

    def _get_values_lines_edi(self):
        invoice_lines = {}
        count = 1

        for invoice_line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
            disc_amount = 0
            total_without_disc = 0

            if not invoice_line.product_uom_id.l10n_co_edi_ubl_id:
                raise UserError(
                    _(
                        'La unidad de medida "%s", no tiene código de unidades de medida'
                        " aceptado por la DIAN."
                    )
                    % invoice_line.product_uom_id.name
                )
            if invoice_line.discount > 100:
                raise ValidationError(
                    _("El descuento en las líneas de la factura no puede ser mayor a 100%.")
                )

            if invoice_line.price_subtotal != 0 and invoice_line.discount != 0:
                disc_amount = (
                    invoice_line.price_unit * invoice_line.quantity * invoice_line.discount
                ) / 100

            if invoice_line.price_unit != 0 and invoice_line.quantity != 0:
                total_without_disc = invoice_line.price_unit * invoice_line.quantity

            if disc_amount > total_without_disc:
                raise ValidationError(
                    _("El descuento supera el valor base en la linea del producto %s")
                    % invoice_line.name
                )

            if total_without_disc < 0:
                raise ValidationError(
                    _("El valor base en la linea del producto %s no debe ser negativo. (%s)")
                    % (invoice_line.name, total_without_disc)
                )

            if invoice_line.price_unit == 0 or invoice_line.quantity == 0:
                raise ValidationError(
                    _(
                        "Líneas de factura con precio o cantidad cero (0) generan rechazo en la facturación electrónica."
                    )
                )

            if not invoice_line.product_id or not invoice_line.product_id.default_code:
                raise UserError(_("La línea de factura %s no tiene referencia") % invoice_line.name)

            invoice_lines[count] = {}
            invoice_lines[count]["Note"] = invoice_line.name or ""
            invoice_lines[count]["unitCode"] = invoice_line.product_uom_id.l10n_co_edi_ubl_id.code
            invoice_lines[count]["Quantity"] = "{:.2f}".format(invoice_line.quantity)
            invoice_lines[count]["LineExtensionAmount"] = "{:.2f}".format(
                invoice_line.price_subtotal
            )
            invoice_lines[count]["MultiplierFactorNumeric"] = "{:.2f}".format(invoice_line.discount)
            invoice_lines[count]["AllowanceChargeAmount"] = "{:.2f}".format(disc_amount)
            invoice_lines[count]["AllowanceChargeBaseAmount"] = "{:.2f}".format(total_without_disc)
            invoice_lines[count]["TaxesTotal"] = {}
            invoice_lines[count]["WithholdingTaxesTotal"] = {}
            invoice_lines[count]["BrandName"] = invoice_line.product_id.l10n_co_edi_brand or ""
            invoice_lines[count]["ModelName"] = invoice_line.product_id.l10n_co_edi_model or ""
            invoice_lines[count]["ItemDescription"] = invoice_line.name
            invoice_lines[count]["SellersItemIdentification"] = invoice_line.product_id.default_code
            invoice_lines[count][
                "StandardItemIdentification"
            ] = invoice_line._l10n_co_edi_get_product_code()
            invoice_lines[count]["PriceAmount"] = "{:.2f}".format(invoice_line.price_unit)

            for tax in invoice_line.tax_ids:  # tax_line_id: # tax_ids
                if tax.amount_type == "group":
                    tax_ids = tax.children_tax_ids
                else:
                    tax_ids = tax

                for tax_id in tax_ids:
                    if tax_id.l10n_co_edi_type:
                        is_withholding = tax_id.l10n_co_edi_type.retention

                        if is_withholding and tax_id.amount == 0:
                            raise UserError(
                                _(
                                    'El importe de la retención "%s" es igual a cero (0), '
                                    "el impuesto de retención debe tener monto diferente a cero (0)."
                                )
                                % tax_id.name
                            )
                        elif is_withholding and tax_id.amount > 0:
                            invoice_lines[count][
                                "WithholdingTaxesTotal"
                            ] = invoice_line._get_taxes_line_edi(
                                invoice_lines[count]["WithholdingTaxesTotal"], tax_id, 1, "item"
                            )
                        elif is_withholding and tax_id.amount < 0:
                            pass
                        elif not is_withholding and tax_id.amount < 0:
                            raise UserError(
                                _(
                                    'El importe del impuesto "%s" es negativo, '
                                    "el impuesto debe tener un monto mayor o igual a cero (0)."
                                )
                                % tax_id.name
                            )
                        elif not is_withholding and tax_id.amount == 0:
                            pass
                        else:
                            invoice_lines[count]["TaxesTotal"] = invoice_line._get_taxes_line_edi(
                                invoice_lines[count]["TaxesTotal"], tax_id, 1, "item"
                            )
                    else:
                        raise UserError(
                            _(
                                'El impuesto "%s", no tiene asignado el tipo fiscal de facturación electrónica..'
                            )
                            % tax.name
                        )

            if "01" not in invoice_lines[count]["TaxesTotal"]:
                invoice_lines[count]["TaxesTotal"]["01"] = {
                    "total": 0.0,
                    "name": "IVA",
                    "taxes": {"0.00": {"base": invoice_line.price_subtotal, "amount": 0.0}},
                }
            if "03" not in invoice_lines[count]["TaxesTotal"]:
                invoice_lines[count]["TaxesTotal"]["03"] = {
                    "total": 0.0,
                    "name": "ICA",
                    "taxes": {"0.00": {"base": invoice_line.price_subtotal, "amount": 0.0}},
                }
            if "04" not in invoice_lines[count]["TaxesTotal"]:
                invoice_lines[count]["TaxesTotal"]["04"] = {
                    "total": 0.0,
                    "name": "INC",
                    "taxes": {"0.00": {"base": invoice_line.price_subtotal, "amount": 0.0}},
                }
            count += 1

        return invoice_lines

    def _get_zipped_file(self, with_pdf=False):
        output = BytesIO()
        zipfile = ZipFile(output, mode="w")
        zipfile_content_xml = BytesIO()
        if self.edi_attachment_file:
            zipfile_content_xml.write(b64decode(self.edi_attachment_file))
            zipfile.writestr("AttachedDocument.xml", zipfile_content_xml.getvalue())
        else:
            zipfile_content_xml.write(b64decode(self.edi_xml_file))
            zipfile.writestr(self.edi_xml_filename, zipfile_content_xml.getvalue())
        if with_pdf:
            zipfile_content_pdf = BytesIO()
            # if not self.edi_pdf_file:
            self.edi_pdf_filename = "{} {}.pdf".format(self.get_name_type_document(), self.name)
            self.edi_pdf_file = self._get_pdf_file()
            zipfile_content_pdf.write(b64decode(self.edi_pdf_file))
            zipfile.writestr(self.edi_pdf_filename, zipfile_content_pdf.getvalue())
        zipfile.close()

        return output.getvalue()

    def action_zip_create(self):
        self.ensure_one()
        self.edi_zipped_file = b64encode(self._get_zipped_file(with_pdf=True)).decode(
            "utf-8", "ignore"
        )

    def _get_billing_reference(self):
        billing_reference = {}
        invoice_reference_id = False
        if self.type_note == "credit":
            invoice_reference_id = self.reversed_entry_id
        elif self.type_note == "debit":
            invoice_reference_id = self.debit_origin_id

        if not invoice_reference_id:
            raise ValidationError(
                _("No es posible identificar la factura referencia de esta Nota.")
            )

        if invoice_reference_id.state == "posted":
            if invoice_reference_id.l10n_co_edi_state == "00":
                billing_reference["ID"] = invoice_reference_id.name  # l10n_co_edi_invoice_name
                billing_reference["UUID"] = invoice_reference_id.edi_cufe_cude_ref
                billing_reference["IssueDate"] = invoice_reference_id.invoice_date
                billing_reference[
                    "CustomizationID"
                ] = invoice_reference_id.l10n_co_edi_operation_type
                self.write(
                    {
                        "name_invoice_reference": invoice_reference_id.name,  # l10n_co_edi_invoice_name,
                        "uuid_invoice_reference": invoice_reference_id.edi_cufe_cude_ref,
                        "issue_date_invoice_reference": invoice_reference_id.invoice_date,
                    }
                )
            else:
                raise ValidationError(
                    _(
                        "El documento electrónico de la factura referencia (%s) "
                        "no está procesado correctamente por la DIAN. \n\n"
                        "Valide que la factura no se encuentre rechazada "
                        "o sin procesar ante la DIAN"
                    )
                    % invoice_reference_id.name
                )  # l10n_co_edi_invoice_name)
        else:
            raise ValidationError(
                _(
                    "Para publicar esta nota se requiere que la factura referencia \
                                    (%s) esté publicada."
                )
                % invoice_reference_id.name
            )  # l10n_co_edi_invoice_name)
        if not billing_reference:
            raise UserError(
                _("La nota %s no tiene referencia de facturación \n\n") % "crédito"
                if self.type_note == "credit"
                else "débito"
                if self.type_note == "debit"
                else ""
            )
        return billing_reference

    def action_sent_zipped_file(self):
        # if self._get_GetStatus(False):
        #     return True

        msg1 = _(
            "Unknown Error,\nStatus Code: %s,\nReason: %s,\n\nContact with your administrator "
            "or you can choose a journal with a Contingency Checkbook E-Invoicing sequence "
            "and change the Invoice Type to 'Factura por Contingencia Facturador'."
        )
        msg2 = _(
            "Unknown Error: %s\n\nContact with your administrator "
            "or you can choose a journal with a Contingency Checkbook E-Invoicing sequence "
            "and change the Invoice Type to 'Factura por Contingencia Facturador'."
        )
        b = "http://schemas.datacontract.org/2004/07/UploadDocumentResponse"
        wsdl = DIAN["wsdl-hab"]

        if self.company_id.profile_execution_id == "1":
            wsdl = DIAN["wsdl"]

            SendBillAsync_values = self._get_SendBillAsync_values()
            SendBillAsync_values["To"] = wsdl.replace("?wsdl", "")
            xml_soap_with_signature = l10n_co_edi_sentences.get_xml_soap_with_signature(
                l10n_co_edi_sentences.render_xml_edi(SendBillAsync_values, "SendBillSync"),
                SendBillAsync_values["Id"],
                self.company_id.certificate_file,
                self.company_id.certificate_password,
            )
        else:
            SendTestSetAsync_values = self._get_SendTestSetAsync_values()
            SendTestSetAsync_values["To"] = wsdl.replace("?wsdl", "")
            xml_soap_with_signature = l10n_co_edi_sentences.get_xml_soap_with_signature(
                l10n_co_edi_sentences.render_xml_edi(SendTestSetAsync_values, "SendTestSetAsync"),
                SendTestSetAsync_values["Id"],
                self.company_id.certificate_file,
                self.company_id.certificate_password,
            )

        try:
            response = post(
                wsdl,
                headers={"content-type": "application/soap+xml;charset=utf-8"},
                data=etree.tostring(xml_soap_with_signature, encoding="unicode"),
            )

            if response.status_code == 200:
                if self.company_id.profile_execution_id == "1":
                    # self.write({'state': 'sent'})
                    self._get_status_response(response, send_mail=False)
                else:
                    root = etree.fromstring(response.text)

                    for element in root.iter("{%s}ZipKey" % b):
                        self.write(
                            {
                                "edi_zip_key": element.text,
                                # 'state': 'sent'
                            }
                        )
                        self.action_GetStatusZip()
            elif response.status_code in (500, 503, 507):
                dian_document_line_obj = self.env["account.invoice.dian.document.line"]
                dian_document_line_obj.create(
                    {
                        "dian_document_id": self.id,
                        "send_async_status_code": response.status_code,
                        "send_async_reason": response.reason,
                        "send_async_response": response.text,
                    }
                )
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))
        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

        return True

    def _get_SendTestSetAsync_values(self):
        xml_soap_values = l10n_co_edi_sentences.get_xml_soap_values(
            self.company_id.certificate_file, self.company_id.certificate_password
        )

        xml_soap_values["fileName"] = self.edi_zipped_filename.replace(".zip", "")
        xml_soap_values["contentFile"] = self.edi_zipped_file.decode("utf-8", "ignore")
        xml_soap_values["testSetId"] = self.company_id.test_set_id

        return xml_soap_values

    def action_GetStatusZip(self):
        wsdl = DIAN["wsdl-hab"]

        if self.company_id.profile_execution_id == "1":
            wsdl = DIAN["wsdl"]

        GetStatusZip_values = self._get_GetStatusZip_values()
        GetStatusZip_values["To"] = wsdl.replace("?wsdl", "")
        xml_soap_with_signature = l10n_co_edi_sentences.get_xml_soap_with_signature(
            l10n_co_edi_sentences.render_xml_edi(GetStatusZip_values, "GetStatusZip"),
            GetStatusZip_values["Id"],
            self.company_id.certificate_file,
            self.company_id.certificate_password,
        )

        response = post(
            wsdl,
            headers={"content-type": "application/soap+xml;charset=utf-8"},
            data=etree.tostring(xml_soap_with_signature, encoding="unicode"),
        )

        if response.status_code == 200:
            self._get_status_response(response, send_mail=False)
        else:
            raise ValidationError(response.status_code)

        return True

    def _get_GetStatusZip_values(self):
        xml_soap_values = l10n_co_edi_sentences.get_xml_soap_values(
            self.company_id.certificate_file, self.company_id.certificate_password
        )

        xml_soap_values["trackId"] = self.edi_zip_key

        return xml_soap_values

    def _get_status_response(self, response, send_mail):
        b = "http://schemas.datacontract.org/2004/07/DianResponse"
        c = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
        s = "http://www.w3.org/2003/05/soap-envelope"
        strings = ""
        to_return = True
        status_code = "other"
        root = etree.fromstring(response.content)
        date_invoice = self.invoice_date

        if not date_invoice:
            date_invoice = fields.Date.today()

        for element in root.iter("{%s}StatusCode" % b):
            if element.text in ("0", "00", "66", "90", "99"):
                if element.text == "00":
                    # self.write({'state': 'done'})

                    if self.l10n_co_edi_state != "00":
                        type_document = self._get_type_document()
                        if type_document == "invoice":  # self.invoice_id.type == "out_invoice":
                            self.sudo().company_id.fv_sent += 1
                        elif (
                            type_document == "credit"
                        ):  # (self.invoice_id.type == "out_refund" and self.invoice_id.refund_type != "debit"):
                            self.company_id.nc_sent += 1
                        elif (
                            type_document == "debit"
                        ):  # (self.invoice_id.type == "out_refund" and self.invoice_id.refund_type == "debit"):
                            self.company_id.nd_sent += 1

                status_code = element.text

        if status_code == "0":
            self.action_GetStatus()  ###
            return True

        if status_code == "00":
            for element in root.iter("{%s}StatusMessage" % b):
                strings = element.text

            for element in root.iter("{%s}XmlBase64Bytes" % b):
                self.write({"edi_ar_file": element.text})

            if self.edi_ar_file:
                self.edi_attachment_file = b64encode(
                    l10n_co_edi_sentences.render_xml_edi(
                        self._get_attachment_values(), "attachment"
                    ).encode()
                ).decode("utf-8", "ignore")
            to_return = True
        else:
            if send_mail:
                self.send_failure_email()  ###
            self.send_failure_email()  ###
            to_return = True

        for element in root.iter("{%s}string" % c):
            if strings == "":
                strings = "- " + element.text
            else:
                strings += "\n\n- " + element.text

        if strings == "":
            for element in root.iter("{%s}Body" % s):
                strings = etree.tostring(element, pretty_print=True)

            if strings == "":
                strings = etree.tostring(root, pretty_print=True)

        self.write({"l10n_co_edi_state": status_code, "l10n_co_edi_response": strings})

        self.edi_zipped_file = b64encode(self._get_zipped_file(with_pdf=True)).decode(
            "utf-8", "ignore"
        )
        if status_code == "00" and not self.mail_sent:  ###
            self.action_send_mail()  ###

        return True

    def action_GetStatus(self):
        wsdl = DIAN["wsdl-hab"]

        if self.company_id.profile_execution_id == "1":
            wsdl = DIAN["wsdl"]

        GetStatus_values = self._get_GetStatus_values()
        GetStatus_values["To"] = wsdl.replace("?wsdl", "")
        xml_soap_with_signature = l10n_co_edi_sentences.get_xml_soap_with_signature(
            l10n_co_edi_sentences.render_xml_edi(GetStatus_values, "GetStatus"),
            GetStatus_values["Id"],
            self.company_id.certificate_file,
            self.company_id.certificate_password,
        )

        response = post(
            wsdl,
            headers={"content-type": "application/soap+xml;charset=utf-8"},
            data=etree.tostring(xml_soap_with_signature, encoding="unicode"),
        )

        if response.status_code == 200:
            self._get_status_response(response, send_mail=False)
        else:
            raise ValidationError(response.status_code)

        return True

    def _get_GetStatus_values(self):
        xml_soap_values = l10n_co_edi_sentences.get_xml_soap_values(
            self.company_id.certificate_file, self.company_id.certificate_password
        )

        xml_soap_values["trackId"] = self.edi_cufe_cude_ref

        return xml_soap_values

    def send_failure_email(self):
        subject = (
            _("ALERTA! La Factura %s no fue enviada a la DIAN.") % self.name
        )  # l10n_co_edi_invoice_name
        msg_body = _(
            """Cordial Saludo,<br/><br/>La factura """
            + self.name
            + """ del cliente """
            + self.partner_id.name
            + """ no pudo ser """
            + """enviada a la Dian según el protocolo establecido previamente. Por """
            """favor revise el estado de la misma en el menú Documentos Dian e """
            """intente reprocesarla según el procedimiento definido."""
            """<br/>""" + self.company_id.name + """."""
        )
        email_to = self.company_id.edi_email_error

        # if email_ids:
        #     email_to = ''

        # for mail_id in email_ids:
        #     email_to += mail_id.email.strip() + ','
        if not email_to:
            raise UserError(
                _(
                    "El(los) correo(s) para fallas de facturas electrónicas no está configurado. \n"
                    "No se le notificará si algo sale mal. \n "
                    "Vaya a Configuración > Compañía > Correos para notificación de errores."
                )
            )

        mail_obj = self.env["mail.mail"]
        msg_vals = {"subject": subject, "email_to": email_to, "body_html": msg_body}
        msg_id = mail_obj.create(msg_vals)
        msg_id.send()

        return True

    def action_send_mail(self):
        msg = _("Su factura no ha sido validada.")
        template_id = self.env.ref("l10n_co_edi_odone.l10n_co_edi_email_template").id
        template = self.env["mail.template"].browse(template_id)

        if not self.name:  # l10n_co_edi_invoice_name:
            raise UserError(msg)

        # xml_attachment_file = False
        # if self.edi_ar_file and self.edi_xml_file:
        #     xml_without_signature = l10n_co_edi_sentences.render_xml_edi(self._get_attachment_values(), 'attachment')

        #     xml_attachment_file = self.env['ir.attachment'].create({
        #         'name': self.name + '-attachment.xml',
        #         'type': 'binary',
        #         'datas': b64encode(xml_without_signature.encode()).decode("utf-8", "ignore")})

        # xml_attachment = self.env['ir.attachment'].create({
        #     'name': self.edi_xml_filename,
        #     'type': 'binary',
        #     'datas': self.edi_xml_file})
        # pdf_attachment = self.env['ir.attachment'].create({
        #     'name': self.name + '.pdf',
        #     'type': 'binary',
        #     'datas': self._get_pdf_file()
        #     })
        if self.edi_zipped_file:
            zip_attachment = self.env["ir.attachment"].create(
                {"name": self.edi_zipped_filename, "type": "binary", "datas": self.edi_zipped_file}
            )

            # attach_ids = [xml_attachment.id, pdf_attachment.id]
            # if xml_attachment_file:
            #     attach_ids.append(xml_attachment_file.id)

            # template.attachment_ids = [(6, 0, attach_ids)]
            if zip_attachment:
                template.attachment_ids = [(6, 0, [zip_attachment.id])]

        template.send_mail(self.id, force_send=True)
        self.write({"mail_sent": True})
        # xml_attachment.unlink()
        # pdf_attachment.unlink()

        # if self.invoice_id.invoice_type_code in ('01', '02'):
        #     #ar_xml_attachment.unlink()
        #     _logger.info('dasda')

        return True

    def _get_SendBillAsync_values(self):
        xml_soap_values = l10n_co_edi_sentences.get_xml_soap_values(
            self.company_id.certificate_file, self.company_id.certificate_password
        )

        xml_soap_values["fileName"] = self.edi_zipped_filename.replace(".zip", "")
        xml_soap_values["contentFile"] = self.edi_zipped_file.decode("utf-8", "ignore")

        return xml_soap_values

    def _get_pdf_file(self):
        template = self.env["ir.actions.report"].browse(self.company_id.report_template.id)
        # pdf = self.env.ref('account.move').render_qweb_pdf([self.invoice_id.id])[0]
        if template:
            pdf = template._render_qweb_pdf(self.id)
        else:
            pdf = self.env.ref("account.account_invoices")._render_qweb_pdf(self.id)
        pdf = b64encode(pdf[0])
        pdf_name = re.sub(r"\W+", "", self.name) + ".pdf"
        return pdf

    def _get_attachment_values(self):
        xml_values = self._get_val_xml_edi()
        xml_values["CustomizationID"] = self.l10n_co_edi_operation_type
        active_resolution = self._get_active_resolution_edi()

        xml_values["InvoiceControl"] = active_resolution
        xml_values["InvoiceTypeCode"] = self.l10n_co_edi_type
        xml_values["InvoiceLines"] = self._get_values_lines_edi()
        xml_values["ApplicationResponse"] = b64decode(self.edi_ar_file).decode("utf-8", "ignore")
        xml_values["xml_file"] = b64decode(self.edi_xml_file).decode("utf-8", "ignore")

        return xml_values
