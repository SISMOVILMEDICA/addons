from odoo import _, api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    specialties_ids = fields.Many2many(related="user_id.specialties_ids")

    @api.model_create_multi
    def create(self, vals):
        for v in vals:
            v["allday"] = False
        return super(CalendarEvent, self).create(vals)
