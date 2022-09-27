from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    signature = fields.Image("Firma", copy=False, attachment=True)
