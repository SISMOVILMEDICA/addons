from odoo import api, fields, models


class HrDocumentType(models.Model):
    _name = "hr.document.type"
    _description = "Document Type"
    _order = "sequence"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    sequence = fields.Integer("Sequence")


class HrDocument(models.Model):
    _name = "hr.document"
    _description = "Document Employee"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    type_id = fields.Many2one("hr.document.type", "Type", required=True)
