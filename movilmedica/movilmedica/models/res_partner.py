from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    country_id = fields.Many2one(
        default=lambda self: self.env.ref("base.co", raise_if_not_found=False)
    )
