from datetime import date
from email.policy import default

from dateutil.relativedelta import relativedelta
from num2words import num2words

from odoo import _, api, fields, models

INCAPACIDAD_NEED_EXCUSE_THRESHOLD = 3

selection_imc = [
    ("bajo", "Bajo peso"),
    ("normal", "Rango normal"),
    ("sobrepeso", "Sobrepeso"),
    ("obesidad", "Obesidad"),
]

selection_parto = [
    ("vaginal", "Vaginal"),
    ("cesarea", "Cesárea"),
]

selection_termino = [
    ("termino", "Término"),
    ("pretermino", "Pretérmino"),
    ("prematuro", "Prematuro"),
]

selection_inmunizaciones = [
    ("c", "Completa"),
    ("i", "Incompleta"),
]

selection_estado = [
    ("bueno", "Bueno"),
    ("aceptable", "Aceptable"),
    ("regular", "Regular"),
    ("malo", "Malo"),
    ("muy_malo", "Muy malo"),
]

selection_normal = [
    ("normal", "Normal"),
    ("Anormal", "Anormal"),
]

metodos_planificacion = [
    ("orales", "Orales"),
    ("inyectables", "Inyectables"),
    ("pomeroy", "Pomeroy"),
    ("parche", "Parche implante"),
    ("condon male", "Condón masculino"),
    ("condon female", "Condón femenino"),
]

valor_predeterminado = "NO REFIERE"
valor_predeterminado_2 = "NO APLICA"


class ClinicHistory(models.Model):
    _name = "clinic.history"
    _description = "Clinic history"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Consecutivo",
        default=_("New"),
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        readonly=True,
    )
    specialty_id = fields.Many2one("hr.specialty", "Specialty")
    birthdate = fields.Date(string="Fecha de nacimiento", required=True)
    age = fields.Integer(
        string="Edad",
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        "State",
        default="draft",
        required=True,
        tracking=True,
    )

    motivo = fields.Text("Motivo")
    motivo_consulta = fields.Text("Motivo de consulta")
    motivo_enfermedad = fields.Text("Enfermedad actual")
    motivo_acompanante = fields.Text("Acompañante")
    motivo_parentesco = fields.Text("Parentesco")

    antecedentes_quirugicos = fields.Text("Quirúrgicos", default=valor_predeterminado)
    antecedentes_familiares = fields.Text("Familiares", default=valor_predeterminado)
    antecedentes_patologicos = fields.Text("Patológicos", default=valor_predeterminado)
    antecedentes_famarcologicos = fields.Text("Farmacológicos", default=valor_predeterminado)
    antecedentes_hospitalarios = fields.Text("Hospitalarios", default=valor_predeterminado)
    antecedentes_alergicos = fields.Text("Alérgicos", default=valor_predeterminado)
    antecedentes_toxicologicos = fields.Text("Toxicológicos", default=valor_predeterminado)
    antecedentes_noxa = fields.Text("noxa", default=valor_predeterminado)
    antecedentes_neurodesarrollo = fields.Text("Neurodesarrollo", default=valor_predeterminado)
    antecedentes_psicosociales = fields.Text("psicosociales", default=valor_predeterminado)
    antecedentes_esquema_vacunacion = fields.Text(
        "esquema de vacunacion", default=valor_predeterminado
    )

    aplica_obstetricos_ginecologicos = fields.Boolean(string="Aplica")
    antecedentes_menarquia = fields.Char("Menarquia")
    antecedentes_fur = fields.Date("FUR")
    antecedentes_fup = fields.Date("FUP")

    antecedentes_obstetrica_a = fields.Char("Fórmula obstétrica")
    antecedentes_obstetrica_b = fields.Char("Fórmula obstétrica")
    antecedentes_obstetrica_c = fields.Char("Fórmula obstétrica")
    antecedentes_obstetrica_d = fields.Char("Fórmula obstétrica")
    antecedentes_obstetrica_e = fields.Char("Fórmula obstétrica")
    antecedentes_obstetrica_f = fields.Char("Fórmula obstétrica")

    antecedentes_metodo = fields.Selection(metodos_planificacion, "Metodo de planificación")
    antecedentes_citologia = fields.Date("Fecha ultima citología")
    antecedentes_mamografia = fields.Date("Fecha ultima mamografía")

    aplica_prenatales_neonatales_vacunacion = fields.Boolean(string="Aplica")
    antecedentes_peso = fields.Char("Peso al nacer")
    antecedentes_gestacion = fields.Char("Gestacion No.")
    antecedentes_parto = fields.Selection(selection_parto, "Parto")
    antecedentes_termino = fields.Selection(selection_termino, "Término")
    antecedentes_complicaciones = fields.Char("Complicaciones al nacer")
    antecedentes_inmunizaciones = fields.Selection(selection_inmunizaciones, "Inmunizaciones")

    revision = fields.Text("Revisión")
    revision_digestivo = fields.Text("Aparato digestivo", default=valor_predeterminado)
    revision_respiratorio = fields.Text("Aparato respiratorio", default=valor_predeterminado)
    revision_cardiovascular = fields.Text("Aparato cardiovascular", default=valor_predeterminado)
    revision_genitourinario = fields.Text("Aparato genitourinario", default=valor_predeterminado)
    revision_tegumentario = fields.Text("Aparato tegumentario", default=valor_predeterminado)
    revision_endocrino = fields.Text("Sistema endocrino", default=valor_predeterminado)
    revision_hematopoyetico = fields.Text("Sistema hematopoyetico", default=valor_predeterminado)
    revision_nervioso = fields.Text("Sistema nervioso", default=valor_predeterminado)

    examen_fc = fields.Integer("FC")
    examen_fr = fields.Integer("FR")
    examen_tension = fields.Char("Tensión arterial")
    examen_tension_tension = fields.Char("Tensión")
    examen_peso = fields.Integer("Peso")
    examen_talla = fields.Integer("Talla")
    examen_imc_float = fields.Float("IMC")
    examen_imc_selection = fields.Selection(selection_imc, "IMC")
    examen_perimetro = fields.Char(
        "Perímetro abdominal",
        default="n/a",
    )
    examen_temperatura = fields.Char(
        "Temperatura",
        default="n/a",
    )
    examen_glucometria = fields.Char(
        "Glucometria",
        default="n/a",
    )
    examen_saturacion_oxigeno = fields.Char(
        "Saturación de oxígeno",
        default="n/a",
    )

    examen_estado_selec = fields.Selection(selection_estado, "Estado general")
    examen_observaciones = fields.Text("Observaciones")
    examen_piel_selec = fields.Selection(selection_normal, "Piel y faneras", default="normal")
    examen_piel_char = fields.Text(
        "Piel",
        default="Sin alteración",
    )
    examen_cabeza_selec = fields.Selection(
        selection_normal, "Cabeza y órganos de los sentidos", default="normal"
    )
    examen_cabeza_char = fields.Text(
        "Cabeza",
        default="Sin alteración",
    )
    examen_cardio_selec = fields.Selection(
        selection_normal, "Cardio respiratorio", default="normal"
    )
    examen_cardio_char = fields.Text(
        "Cardio",
        default="Ruidos cardíacos rítmicos, sin soplos. Ruidos respiratorios sin agregados pulmonares",
    )
    examen_abdomen_selec = fields.Selection(selection_normal, "Abdomen", default="normal")
    examen_abdomen_char = fields.Text(
        "Abdomen",
        default="Blando, depresible, no doloroso a la palpación. No masas ni megalias. Ruidos intestinales positivos",
    )
    examen_urogenital_selec = fields.Selection(selection_normal, "Urogenital", default="normal")
    examen_urogenital_char = fields.Text(
        "Urogenital",
        default="No explorado - Sin Alteración",
    )
    examen_extremidades_selec = fields.Selection(
        selection_normal, "Extremidades y osteoarticular", default="normal"
    )
    examen_extremidades_char = fields.Text(
        "Extremidades",
        default="Sin alteración",
    )
    examen_neurologico_selec = fields.Selection(selection_normal, "Neurológico", default="normal")
    examen_neurologico_char = fields.Text(
        "Neurológico",
        default="Alerta, orientado en las tres esferas, sin déficit neurológico. Pares craneales son alteración",
    )

    impresion = fields.Text("Impresión")
    impresion_principal = fields.Many2one("cie.rips", "Principal")
    impresion_relacionado1 = fields.Many2one("cie.rips", "Relacionado 1")
    impresion_relacionado2 = fields.Many2one("cie.rips", "Relacionado 2")
    impresion_relacionado3 = fields.Many2one("cie.rips", "Relacionado 3")
    impresion_relacionado4 = fields.Many2one("cie.rips", "Relacionado 4")

    analisis = fields.Text("Revisión")
    analisis_general = fields.Text("Análisis general", default=valor_predeterminado)
    analisis_resultados = fields.Text("Resultados de laboratorios", default=valor_predeterminado)

    plan = fields.Text("Plan")
    plan_manejo = fields.Text("Plan de manejo", default=valor_predeterminado)
    plan_medicamentos = fields.Text("Medicamentos", default=valor_predeterminado)
    plan_recomendaciones = fields.Many2many(
        "clinic.history.recommendation", string="Recomendaciones"
    )
    plan_recomendacion = fields.Text(string="Recomendación")
    plan_terapia = fields.Text("Terapia")
    plan_sesiones = fields.Integer("Número de sesiones")

    procedimientos = fields.Text("Procedimientos")

    interconsultas = fields.Text("Interconsultas", default=valor_predeterminado)
    medicines_pbs = fields.Text(
        "Medicamentos PBS",
        required=True,
    )
    medicines_no_pbs = fields.Text(
        "Medicamentos NO PBS",
        required=True,
        default="Por solicitud del paciente se sugiere medicamento comercial y se especifica que no lo suministra su EPS",
    )
    interconsultas_terapias = fields.Text("Terapias", default=valor_predeterminado)
    interconsultas_laboratorios = fields.Text("Laboratorio clínico", default=valor_predeterminado)
    interconsultas_imagenes = fields.Text("Imagenología", default=valor_predeterminado)

    need_remisiones_basica = fields.Boolean("Ambulancia básica")
    remisiones_basica = fields.Char("Observaciones")
    need_remisiones_medicalizada = fields.Boolean("Ambulancia medicalizada")
    remisiones_medicalizada = fields.Char("Observaciones")
    need_remisiones_urgencias = fields.Boolean("Urgencias")
    remisiones_urgencias = fields.Char("Observaciones")
    need_remisiones_others = fields.Boolean("Otros")
    remisiones_others = fields.Char("Observaciones")

    incapacidad = fields.Boolean("Incapacidad", default=False)
    disease_id = fields.Many2one("cie.rips", "Disease")
    incapacidad_desde = fields.Date(
        "Desde",
        default=fields.Date.today,
        readonly=True,
    )
    incapacidad_hasta = fields.Date("Hasta")
    incapacidad_dias = fields.Integer(
        string="Número de días",
        compute="_compute_incapacidad_dias",
    )
    incapacidad_dias_char = fields.Char(
        string="Número en letras",
        compute="_compute_incapacidad_dias_char",
    )
    incapacidad_need_excuse = fields.Boolean(
        compute="_compute_incapacidad_need_excuse",
    )
    incapacidad_excuse = fields.Text(
        string="Justificación médica",
    )
    medications_applied_in_consultation = fields.Many2many(
        comodel_name="product.product",
    )

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("clinic.history") or _("New")
        return super(ClinicHistory, self).create(vals)

    def action_done(self):
        self.write({"state": "done"})
        self.message_post(body=_("This is your medical history"))

    @api.onchange("examen_peso", "examen_talla")
    def _onchange_examen_imc(self):
        if self.examen_peso and self.examen_talla:
            imc = self.examen_peso / pow((self.examen_talla / 100), 2)
            if imc < 18.5:
                examen_imc = "bajo"
            elif imc >= 18.5 and imc < 24.9:
                examen_imc = "normal"
            elif imc >= 24.9 and imc <= 29.9:
                examen_imc = "sobrepeso"
            else:
                examen_imc = "obesidad"
            self.examen_imc_float = imc
            self.examen_imc_selection = examen_imc

    @api.onchange("plan_recomendaciones")
    def _onchange_recomendaciones(self):
        if self.plan_recomendaciones:
            self.plan_recomendacion = ""
        for recomendacion in self.plan_recomendaciones:
            self.plan_recomendacion += "\n" + recomendacion.recommendation

    @api.depends("incapacidad_desde", "incapacidad_hasta")
    def _compute_incapacidad_dias(self):
        for history in self:
            if not (history.incapacidad_desde and history.incapacidad_hasta):
                history.incapacidad_dias = 0
                continue
            incapacidad_delta = history.incapacidad_hasta - history.incapacidad_desde
            history.incapacidad_dias = incapacidad_delta.days + 1

    @api.depends("incapacidad_dias")
    def _compute_incapacidad_dias_char(self):
        for history in self:
            history.incapacidad_dias_char = num2words(history.incapacidad_dias, lang="es_CO")

    @api.depends("incapacidad_dias")
    def _compute_incapacidad_need_excuse(self):
        for history in self:
            history.incapacidad_need_excuse = (
                history.incapacidad_dias > INCAPACIDAD_NEED_EXCUSE_THRESHOLD
            )
