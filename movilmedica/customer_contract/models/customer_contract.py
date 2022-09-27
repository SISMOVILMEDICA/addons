from odoo import api, fields, models

from .res_partner import TYPE_COMPANY

HELP_CDP = "Certificado de disponibilidad presupuestal"
HELP_RP = "Registro Presupuestal de Compromiso"


class CustomerContract(models.Model):
    _name = "customer.contract"
    _description = "Contratos de clientes"
    _order = "name"

    name = fields.Char(string="Número", required=True)
    description = fields.Text(string="Descripción", required=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente",
        domain="[('is_company', '=', True)]",
        required=True,
    )
    type_company = fields.Selection(string="Tipo de empresa", related="partner_id.type_company")
    cdp_number = fields.Char(string="Número", help=HELP_CDP)
    cdp_amount = fields.Float(string="Monto")
    cdp_file = fields.Binary(string="Documento")

    diagnostics_ids = fields.Many2many("customer.contract.diagnostic", string="Ayudas Diagnosticas")

    rp_number = fields.Char(string="Número", help=HELP_RP)
    rp_amount = fields.Float(string="Monto")
    rp_file = fields.Binary(string="Documento")

    amount = fields.Float(string="Monto", required=True)
    start_date = fields.Date(string="Inicio", required=True)
    end_date = fields.Date(string="Fin", required=True)

    report_budget_ids = fields.One2many(
        comodel_name="customer.contract.report.budget", inverse_name="customer_contract_id"
    )
    report_budget_cdp_ids = fields.One2many(
        comodel_name="customer.contract.report.budget",
        compute="_get_report_budget",
        string=HELP_CDP,
    )
    report_budget_rp_ids = fields.One2many(
        comodel_name="customer.contract.report.budget", compute="_get_report_budget", string=HELP_RP
    )

    annex_ids = fields.One2many(
        comodel_name="customer.contract.annex", inverse_name="customer_contract_id", string="Otrosí"
    )
    annex_time_seq = fields.Integer(string="Secuencia de otrosi prorroga", default=0)
    annex_time_ids = fields.One2many(
        comodel_name="customer.contract.annex", compute="_get_annex", string="Prórroga"
    )
    annex_money_seq = fields.Integer(string="Secuencia de otrosi adicion", default=0)
    annex_money_ids = fields.One2many(
        comodel_name="customer.contract.annex", compute="_get_annex", string="Adición"
    )

    policy_ids = fields.One2many(
        comodel_name="customer.contract.policy",
        inverse_name="customer_contract_id",
        string="Pólizas",
    )
    products_ids = fields.Many2many(comodel_name="product.product", string="Productos")

    @api.depends("report_budget_ids")
    def _get_report_budget(self):
        for record in self:
            cdp = []
            rp = []
            for rb in record.report_budget_ids:
                cdp.append(rb.id) if rb.type == "CDP" else rp.append(rb.id)
            record.report_budget_cdp_ids = self.env["customer.contract.report.budget"].browse(cdp)
            record.report_budget_rp_ids = self.env["customer.contract.report.budget"].browse(rp)

    @api.depends("annex_ids")
    def _get_annex(self):
        for record in self:
            t = []
            m = []
            for an in record.annex_ids:
                t.append(an.id) if an.type == "time" else m.append(an.id)
            record.annex_time_ids = self.env["customer.contract.annex"].browse(t)
            record.annex_money_ids = self.env["customer.contract.annex"].browse(m)

    def get_next_seq_annex(self, type):
        if type == "time":
            self.write({"annex_time_seq": self.annex_time_seq + 1})
            return self.annex_time_seq
        else:
            self.write({"annex_money_seq": self.annex_money_seq + 1})
            return self.annex_money_seq
