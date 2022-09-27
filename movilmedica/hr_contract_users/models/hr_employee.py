from odoo import api, fields, models

blood_type_selection = [
    ("on", "O-"),
    ("op", "O+"),
    ("an", "A-"),
    ("ap", "A+"),
    ("bn", "B-"),
    ("bp", "B+"),
    ("abn", "AB-"),
    ("abp", "AB+"),
]


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    allergies_ids = fields.Many2many("hr.allergy", string="Allergies")
    bank_ids = fields.One2many(related="user_partner_id.bank_ids")
    blood_type = fields.Selection(blood_type_selection, "Blood type", default="on")
    documents_ids = fields.One2many("hr.employee.document", "employee_id", "Documents")
    employee_modality = fields.Selection(
        [("presence", "Presence"), ("virtual", "Virtual")], "Modality", default="presence"
    )
    employee_rut = fields.Char("RUT")
    employee_type = fields.Selection(
        [("internal", "Internal"), ("external", "External")], "Employee Type", default="internal"
    )
    illness_ids = fields.Many2many("hr.illness", string="Illness")
    specialties_ids = fields.Many2many("hr.specialty", string="Specialties")

    signature_file = fields.Binary("Signature", attachment=True)
    signature_name = fields.Char("Signature name")
    stamp_file = fields.Binary("Stamp", attachment=True)
    stamp_name = fields.Char("Stamp name")


class HrEmployeeDocument(models.Model):
    _name = "hr.employee.document"
    _description = "Document Employee"

    employee_id = fields.Many2one("hr.employee", "Employee", required=True, ondelete="cascade")
    type_id = fields.Many2one("hr.document.type", "Type", required=True)
    document_id = fields.Many2one("hr.document", "Document", required=True)
    name = fields.Char("Name", required=True)
    file_data = fields.Binary("File", attachment=True)
    file_name = fields.Char("File Name")
