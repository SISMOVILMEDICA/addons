from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ClinicHistory(models.Model):
    _inherit = "clinic.history"

    file_number = fields.Char("File number")
    diagnostics_ids = fields.Many2many("customer.contract.diagnostic", string="Diagnostic")
    project_id = fields.Many2one(related="task_id.project_id")
    project_diagnostics_ids = fields.Many2many(related="project_id.diagnostics_ids")
    task_id = fields.Many2one("project.task", "Task")
    project_partner_id = fields.Many2one(related="task_id.project_partner_id", string="Partner")
    date_coming = fields.Datetime("Coming date")
    date_exit = fields.Datetime("Exit date")

    interconsultas_therapies_cups = fields.Many2many(
        relation="clinic_history_customer_contract_cups_therapies_rel",
        comodel_name="customer.contract.cups",
        column1="history_id",
        column2="cup_id",
        string="CUPS de terapias",
    )
    interconsultas_interconsultations_cups = fields.Many2many(
        relation="clinic_history_customer_contract_cups_interconsultations_rel",
        comodel_name="customer.contract.cups",
        column1="history_id",
        column2="cup_id",
        string="CUPS de interconsultas",
    )
    interconsultas_laboratorios_cups = fields.Many2many(
        relation="clinic_history_customer_contract_cups_clinical_laboratories_rel",
        comodel_name="customer.contract.cups",
        column1="history_id",
        column2="cup_id",
        string="CUPS de laboratorio clínico",
    )
    interconsultas_imagenes_cups = fields.Many2many(
        relation="clinic_history_customer_contract_cups_images_rel",
        comodel_name="customer.contract.cups",
        column1="history_id",
        column2="cup_id",
        string="CUPS de imagenología",
    )

    def action_done(self):
        res = super(ClinicHistory, self).action_done()
        self.task_id.write({"stage_id": self.env.ref("industry_fsm.planning_project_stage_1").id})
        return res

    def button_coming(self):
        for history in self:
            history._action_coming()

    def _action_coming(self):
        self.ensure_one()
        self.task_id.action_timer_start()
        self.write({"date_coming": fields.Datetime.now()})

    def button_exit(self):
        self.write({"date_exit": fields.Datetime.now()})
        return self.task_id.action_timer_stop()

    def write(self, vals):
        if not self.task_id:
            raise ValidationError("La historia clínica no tiene un servicio relacionado")
        if not self.task_id.planned_date_begin:
            raise ValidationError("El servicio de la historia clínica no tiene una fecha de inicio")
        default_lab = [(None, None, self.interconsultas_laboratorios_cups.ids)]
        default_img = [(None, None, self.interconsultas_imagenes_cups.ids)]
        cups = []
        cups += vals.get("interconsultas_laboratorios_cups", default_lab)[0][2]
        cups += vals.get("interconsultas_imagenes_cups", default_img)[0][2]
        if cups:
            self.task_id.product_ids.unlink()
            self.task_id.product_ids = self.build_products(cups, self.task_id.planned_date_begin)
        return super(ClinicHistory, self).write(vals)

    def build_products(self, cups_ids, date):
        """
        Return list of products as dicts
        params:
            cups_ids: list or tuple of int
        return --> list of tuple
        """
        cups_model = self.env["customer.contract.cups"]
        # {int: (0,0,{'product_id':int, 'price':float, 'quantity':int}})
        products = {}
        for cups in cups_model.browse(cups_ids):
            product_id = cups.product_id.id
            if not product_id:
                continue
            if product_id in products:
                products[product_id][2]["quantity"] += 1
            else:
                price = cups._get_price_from_date(date)
                products[product_id] = (
                    0,
                    0,
                    {"product_id": product_id, "price": price, "quantity": 1},
                )
        return list(products.values())

    def action_format_send(self):
        self.ensure_one()
        if not (self.task_id.partner_id and self.task_id.partner_id.email):
            raise ValidationError(
                "Dirijase al servicio y configure el correo electrónico del paciente"
            )

        ir_model_data = self.env["ir.model.data"]
        try:
            template_id = ir_model_data.get_object_reference(
                "industry_fsm_movilmedica", "mail_template_clinic_historiy"
            )[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                "mail", "email_compose_message_wizard_form"
            )[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            "default_model": "project.task",
            "default_res_id": self.task_id.id,
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "mark_so_as_sent": True,
            "force_email": True,
        }
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
        }
