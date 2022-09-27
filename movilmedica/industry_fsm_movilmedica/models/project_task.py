import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    name = fields.Char(default=_("New"))
    planned_date_begin = fields.Datetime(string="Fecha de Atención", required=True)
    observation = fields.Text("Observation")
    # Assign
    assign_bool = fields.Boolean("Assign", default=False)
    # Date
    date_light = fields.Selection(
        [("red", "Red"), ("yellow", "Yellow"), ("green", "Green")],
        "Light Date",
        compute="_compute_date_light",
    )
    # File
    file_number = fields.Char("File number", required=True)
    # Fleet
    fleet_name = fields.Char("Fleet")
    # History
    history_id = fields.Many2one("clinic.history", "History", compute="_compute_history")
    history_ids = fields.One2many("clinic.history", "task_id", "Histories")
    # Pay00
    pay_co = fields.Boolean("Copay", default=False)
    pin_pay_co = fields.Char(string="Pin de copago")
    pay_amount = fields.Float("Amount Pay", digits="Product Price")
    # Partner
    partner_identification_type_id = fields.Many2one(
        related="partner_id.l10n_latam_identification_type_id", readonly=False, required=True
    )
    partner_name = fields.Char(related="partner_id.name", readonly=False)
    partner_vat = fields.Char(related="partner_id.vat", readonly=False, required=True)
    partner_affiliation = fields.Selection(related="partner_id.patient_affiliation", readonly=False, required=True)
    partner_birthdate = fields.Date(related="partner_id.patient_birthdate", readonly=False, required=True)
    partner_age = fields.Integer(related="partner_id.patient_age_years")
    partner_martial_status = fields.Selection(related="partner_id.patient_martial_status", readonly=False, required=True)
    partner_gender = fields.Selection(related="partner_id.patient_gender", readonly=False, required=True)
    partner_mobile = fields.Char(related="partner_id.mobile", readonly=False, required=True)
    partner_email = fields.Char(related="partner_id.email", readonly=False, required=True)
    partner_street = fields.Char(string="Dirección", related="partner_id.street", readonly=False, required=True)
    partner_neighborhood_id = fields.Many2one(related="partner_id.neighborhood_id", readonly=False, required=True)
    partner_locality_id = fields.Many2one(related="partner_id.locality_id", readonly=False, required=True)
    partner_city_id = fields.Many2one(related="partner_id.city_id", readonly=False, string="Ciudad", required=True)
    partner_uom_id = fields.Many2one(related="partner_id.patient_uom_id", readonly=False, required=True)
    # Project
    project_id = fields.Many2one(required=True)
    project_partner_id = fields.Many2one(related="project_id.partner_id", string="Partner")
    partner_id = fields.Many2one(required=True)
    sub_agreement = fields.Char(string="Subconvenio", required=True)
    # Specialty
    specialty_id = fields.Many2one("hr.specialty", "Specialty", required=True)
    specialties_ids = fields.Many2many(related="project_id.specialties_ids")
    # Users
    users_ids = fields.Many2many("res.users", string="Users", compute="_compute_users_ids")
    user_id = fields.Many2one(required=True)
    # Products
    product_ids = fields.One2many(
        comodel_name="project.task.product", inverse_name="task_id", string="Productos por CUPS"
    )
    product_extra_ids = fields.One2many(
        comodel_name="project.task.product.extra",
        inverse_name="task_id",
        string="Productos adicionales",
    )
    planned_date_end = fields.Datetime(
        compute="_compute_planned_date_end",
        store=True,
    )

    @api.depends("planned_date_begin")
    def _compute_planned_date_end(self):
        for task in self:
            if not task.planned_date_begin:
                task.planned_date_end = False
                continue
            task.planned_date_end = task.planned_date_begin + datetime.timedelta(hours=1) # TODO

    @api.depends("history_ids")
    def _compute_history(self):
        for task in self:
            task.history_id = task.history_ids[0] if task.history_ids else False

    @api.depends("date_assign", "planned_date_begin", "stage_id")
    def _compute_date_light(self):
        task_date_assign = self.filtered(lambda t: not t.date_assign)
        task_date_begin = self.filtered(lambda t: not t.planned_date_begin)
        task_done_cancel = self.filtered(lambda t: t._is_done_cancel())
        for task in self - (task_date_assign | task_date_begin | task_done_cancel):
            date_now = fields.Datetime.now()
            date_assign = task.date_assign
            date_begin = task.planned_date_begin
            date_time = date_begin - date_assign
            date_green = date_assign + datetime.timedelta(seconds=date_time.seconds * (2 / 4))
            date_yellow = date_assign + datetime.timedelta(seconds=date_time.seconds * (3 / 4))
            date_red = date_begin
            if date_now <= date_green:
                date_light = "green"
            elif date_now > date_green and date_now <= date_yellow:
                date_light = "yellow"
            else:
                date_light = "red"
            task.update({"date_light": date_light})
        (task_date_assign | task_date_begin | task_done_cancel).update({"date_light": False})

    @api.depends("planned_date_begin", "planned_date_end")
    def _compute_users_ids(self):
        for task in self:
            domain = [
                ("start", "<=", task.planned_date_begin),
                ("stop", ">=", task.planned_date_end),
            ]
            task.users_ids = self.env["calendar.event"].sudo().search(domain).user_id


    def _is_done_cancel(self):
        self.ensure_one()
        stage_done = self.env.ref("industry_fsm.planning_project_stage_1").id
        stage_cancel = self.env.ref("industry_fsm_movilmedica.planning_project_stage_4").id
        stages = [stage_done, stage_cancel]
        return self.stage_id.id in stages

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("project.task") or _("New")
        return super(ProjectTask, self).create(vals)

    def action_assign(self):
        self.write(
            {
                "assign_bool": True,
                "date_assign": fields.Datetime.now(),
                "stage_id": self.env.ref("industry_fsm_movilmedica.planning_project_stage_2").id,
            }
        )
        self.message_post(body=_("You have been assigned a task"))

    def create_history(self):
        self.ensure_one()
        if not self.product_extra_ids:
            raise ValidationError("Se requiere al menos un producto adicional.")

        action = self.env["ir.actions.actions"]._for_xml_id(self.specialty_id.action_char)
        action["context"] = {
            "default_specialty_id": self.specialty_id.id if self.specialty_id else False,
            "default_task_id": self.id,
            "default_partner_id": self.partner_id.id if self.partner_id else False,
        }
        return action

    def action_history(self):
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'clinic.history',
            'res_id': self.history_id.id,
        }
