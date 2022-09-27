from odoo import _, api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    contract_id = fields.Many2one("customer.contract", "Contract")
    diagnostics_ids = fields.Many2many(related="contract_id.diagnostics_ids")
    specialties_ids = fields.Many2many(related="contract_id.specialties_ids")
