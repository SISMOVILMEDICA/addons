import logging
from datetime import datetime

import pytz
from dateutil import tz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    edi_resolution_control = fields.Boolean(
        string="¿Usar el control de resoluciones DIAN?", default=False
    )
    edi_type = fields.Selection(
        [
            ("e_inv", _("Facturación electrónica")),
            ("pc_inv", "Computer Generated Invoice"),
        ],
        string="Tipo EDI",
    )

    @api.model
    def create(self, vals):
        rec = super(IrSequence, self).create(vals)

        for record in rec:
            if record.edi_resolution_control:
                record.check_active_resolution()
            record.check_date_range_ids()
        return rec

    def write(self, vals):
        res = super(IrSequence, self).write(vals)

        for record in self:
            if record.edi_resolution_control:
                record.check_active_resolution()
            record.check_date_range_ids()
        return res

    @api.onchange("edi_resolution_control")
    def onchange_edi_resolution_control(self):
        for record in self:
            if record.edi_resolution_control:
                record.use_date_range = True
                record.implementation = "no_gap"

    def check_active_resolution(self):
        self.ensure_one()

        if self.edi_resolution_control:
            if self.padding != 0:
                self.padding = 0
            if self.implementation != "no_gap":
                self.implementation = "no_gap"
            if not self.use_date_range:
                self.use_date_range = True
            if self.suffix:
                self.suffix = False
            if self.number_increment != 1:
                self.number_increment = 1

            timezone = pytz.timezone(self.env.user.tz or "America/Bogota")
            from_zone = tz.gettz("UTC")
            to_zone = tz.gettz(timezone.zone)
            current_date = datetime.now().replace(tzinfo=from_zone)
            current_date = current_date.astimezone(to_zone).strftime("%Y-%m-%d")

            for date_range_id in self.date_range_ids:
                number_next_actual = date_range_id.number_next_actual

                if (
                    number_next_actual >= date_range_id.number_from
                    and number_next_actual <= date_range_id.number_to
                    and current_date >= str(date_range_id.date_from)
                    and current_date <= str(date_range_id.date_to)
                ):
                    if not date_range_id.active_resolution:
                        date_range_id.active_resolution = True
                    if date_range_id.prefix != self.prefix:
                        date_range_id.prefix = self.prefix
                else:
                    date_range_id.active_resolution = False
                if not date_range_id.prefix:
                    date_range_id.prefix = self.prefix
        return True

    def check_date_range_ids(self):
        msg1 = _("La fecha final debe ser mayor o igual que la fecha inicial.")
        msg2 = _("El número final debe ser mayor o igual que el número inicial.")
        msg3 = _(
            "El Número siguiente debe ser mayor en uno al número final, para representar una secuencia terminada o Número siguiente debe incluirse en el Rango de números."
        )
        msg4 = _(
            "El intervalo de fechas debe ser único o no se debe incluir una fecha en otro intervalo de fechas."
        )
        msg5 = _("El sistema solo necesita una resolución DIAN activa.")
        msg6 = _("El sistema necesita al menos una resolución DIAN activa.")
        date_ranges = []
        _active_resolution = 0
        for date_range_id in self.date_range_ids:
            if date_range_id.date_from and date_range_id.date_to:
                if date_range_id.date_from > date_range_id.date_to:
                    raise ValidationError(msg1)
                date_ranges.append((date_range_id.date_from, date_range_id.date_to))
            if date_range_id.number_from and date_range_id.number_to:
                if date_range_id.number_from > date_range_id.number_to:
                    raise ValidationError(msg2)
                elif (
                    date_range_id.number_next_actual > (date_range_id.number_to + 1)
                    or date_range_id.number_from > date_range_id.number_next_actual
                ):
                    raise ValidationError(msg3)
            if date_range_id.active_resolution and self.edi_resolution_control:
                _active_resolution += 1

        date_ranges.sort(key=lambda date_range: date_range[0])
        date_from = False
        date_to = False

        for date_range in date_ranges:
            if not date_from and not date_to:
                date_from = date_range[0]
                date_to = date_range[1]
                continue
            if date_to < date_range[0]:
                date_from = date_range[0]
                date_to = date_range[1]
            else:
                raise ValidationError(msg4)

        if self.edi_resolution_control:
            if _active_resolution > 1:
                raise ValidationError(msg5)
            if _active_resolution == 0:
                raise ValidationError(msg6)

    def _next(self, sequence_date=None):
        msg = _("No existe una resolución de facturación autorizada activa.")
        date_ranges = self.date_range_ids.search([("active_resolution", "=", True)])

        if self.edi_resolution_control and not date_ranges:
            raise ValidationError(msg)

        res = super(IrSequence, self)._next()

        if self.edi_resolution_control:
            self.check_active_resolution()
        return res
