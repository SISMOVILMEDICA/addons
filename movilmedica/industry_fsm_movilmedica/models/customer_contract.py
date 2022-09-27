from odoo import _, api, fields, models


class CustomerContract(models.Model):
    _inherit = "customer.contract"

    specialties_ids = fields.Many2many("hr.specialty", string="Specialties")
