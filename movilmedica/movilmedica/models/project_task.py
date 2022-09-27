from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    driver_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("category_id.name", "ilike", "Conductor")],
        string="Conductor",
        required=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        compute="_compute_pricelist_id",
        store=True,
    )
    product_template_available_ids = fields.Many2many(
        related="pricelist_id.product_template_ids",
    )
    product_available_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_compute_product_available_ids",
    )
    authorizer = fields.Char(
        string="Persona que autoriza",
        required=True,
    )
    type_pay_co = fields.Selection(
        selection=[
            ("pin", "PIN"),
            ("cash", "Efectivo"),
        ],
    )
    pin_pay_co = fields.Char(
        string="PIN",
    )
    authorization_pay_co = fields.Char(
        string="Autorización",
    )
    cash_pay_co = fields.Monetary(
        string="Efectivo",
        currency_field="currency_id",
    )
    initial_reason_for_consultation = fields.Text(
        string="Motivo inicial de consulta",
        required=True,
    )
    patient_need_responsable = fields.Boolean(
        string="¿El paciente necesita un responsable?",
    )
    responsable_name = fields.Char(string="Nombre")
    responsable_vat = fields.Char(string="Cédula")
    responsable_relationship = fields.Char(string="Parentesco")
    responsable_mobile = fields.Char(string="Teléfono")

    @api.depends("product_template_available_ids")
    def _compute_product_available_ids(self):
        for task in self:
            task.product_available_ids = task.product_template_available_ids.product_variant_ids

    @api.depends("project_partner_id")
    def _compute_pricelist_id(self):
        for task in self:
            if task.project_partner_id:
                task.pricelist_id = task.project_partner_id.property_product_pricelist.id
