from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_einvoicing = fields.Boolean(
        string="Facturación Electrónica",
        help="Habilita la opción configurar la resolución DIAN para facturación electrónica",
    )
    edi_code = fields.Char(
        string="Código corto", size=5, help="Se utiliza para crear el prefijo de las secuencias"
    )
    resolution_text = fields.Text(
        string="Información de Resolución",
        help="Texto informativo sobre la resolución de facturación electrónica que aparecerá en la representación gráfica.",
    )

    # Se crean en el módulo od_journal_sequence
    # sequence_id = fields.Many2one('ir.sequence', string='Secuencia de Factura',
    #     help="Este campo contiene la información relacionada con la numeración de las facturas electrónicas de este diario.", required=True, copy=False)
    # sequence_number_next = fields.Integer(string='Próximo número',
    #     help='El siguiente número de secuencia se utilizará para la próxima factura.',
    #     compute='_compute_seq_number_next',
    #     inverse='_inverse_seq_number_next')

    # refund_sequence = fields.Boolean(string='Secuencia de nota crédito dedicada', help="Marque esta casilla si no desea compartir la misma secuencia para las facturas y notas de crédito electrónicas realizadas desde este diario.", default=False)
    # refund_sequence_id = fields.Many2one('ir.sequence', string='Secuencia de Nota Crédito',
    #     help="Este campo contiene la información relacionada con la numeración de las notas de crédito electrónicas de este diario.", copy=False)
    # refund_sequence_number_next = fields.Integer(string='Próximo número de Nota Crédito',
    #     help='El siguiente número de secuencia se utilizará para la siguiente nota de crédito.',
    #     compute='_compute_refund_seq_number_next',
    #     inverse='_inverse_refund_seq_number_next')

    debit_note_sequence = fields.Boolean(
        string="Secuencia de nota débito dedicada",
        help="Marque esta casilla si no desea compartir la misma secuencia para las facturas y notas de débito electrónicas realizadas desde este diario.",
        default=False,
    )
    debit_note_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Secuencia de Nota Débito",
        help="Este campo contiene la información relacionada con la numeración de las notas de débito electrónicas de este diario.",
        copy=False,
    )
    debit_note_sequence_number_next = fields.Integer(
        string="Próximo número de Nota Débito",
        help="El siguiente número de secuencia se utilizará para la siguiente nota de débito.",
        compute="_compute_debit_seq_number_next",
        inverse="_inverse_debit_seq_number_next",
    )

    remaining_numbers = fields.Integer(string="Números restantes", default=False)
    remaining_days = fields.Integer(string="Días restantes", default=False)

    edi_technical_key = fields.Char(string="Llave técnica")

    # @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    # def _compute_seq_number_next(self):
    #     '''Compute 'sequence_number_next' according to the current sequence in use,
    #     an ir.sequence or an ir.sequence.date_range.
    #     '''
    #     for journal in self:
    #         if journal.sequence_id:
    #             sequence = journal.sequence_id._get_current_sequence()
    #             journal.sequence_number_next = sequence.number_next_actual
    #         else:
    #             journal.sequence_number_next = 1

    # def _inverse_seq_number_next(self):
    #     '''Inverse 'sequence_number_next' to edit the current sequence next number.
    #     '''
    #     for journal in self:
    #         if journal.sequence_id and journal.sequence_number_next:
    #             sequence = journal.sequence_id._get_current_sequence()
    #             sequence.sudo().number_next = journal.sequence_number_next

    # @api.depends('refund_sequence_id.use_date_range', 'refund_sequence_id.number_next_actual')
    # def _compute_refund_seq_number_next(self):
    #     '''Compute 'sequence_number_next' according to the current sequence in use,
    #     an ir.sequence or an ir.sequence.date_range.
    #     '''
    #     for journal in self:
    #         if journal.refund_sequence_id and journal.refund_sequence:
    #             sequence = journal.refund_sequence_id._get_current_sequence()
    #             journal.refund_sequence_number_next = sequence.number_next_actual
    #         else:
    #             journal.refund_sequence_number_next = 1

    # def _inverse_refund_seq_number_next(self):
    #     '''Inverse 'refund_sequence_number_next' to edit the current sequence next number.
    #     '''
    #     for journal in self:
    #         if journal.refund_sequence_id and journal.refund_sequence and journal.refund_sequence_number_next:
    #             sequence = journal.refund_sequence_id._get_current_sequence()
    #             sequence.sudo().number_next = journal.refund_sequence_number_next

    @api.depends(
        "debit_note_sequence_id.use_date_range", "debit_note_sequence_id.number_next_actual"
    )
    def _compute_debit_seq_number_next(self):
        """Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        """
        for journal in self:
            if journal.debit_note_sequence_id and journal.debit_note_sequence:
                sequence = journal.debit_note_sequence_id._get_current_sequence()
                journal.debit_note_sequence_number_next = sequence.number_next_actual
            else:
                journal.debit_note_sequence_number_next = 1

    def _inverse_debit_seq_number_next(self):
        """Inverse 'debit_note_sequence_number_next' to edit the current sequence next number."""
        for journal in self:
            if (
                journal.debit_note_sequence_id
                and journal.debit_note_sequence
                and journal.debit_note_sequence_number_next
            ):
                sequence = journal.debit_note_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.debit_note_sequence_number_next

    def write(self, vals):
        for journal in self:
            if "code" in vals and journal.edi_code != vals["code"]:
                if self.env["account.move"].search([("journal_id", "in", self.ids)], limit=1):
                    raise UserError(
                        _(
                            "This journal already contains items, therefore you cannot modify its short name."
                        )
                    )
                # new_prefix = self._get_sequence_prefix(vals['code'], type_note=False)
                # journal.sequence_id.write({'prefix': new_prefix})
                # if journal.refund_sequence_id:
                #     new_prefix = self._get_sequence_prefix(vals['edi_code'], type_note='credit')
                #     journal.refund_sequence_id.write({'prefix': new_prefix})
                if journal.debit_note_sequence_id:
                    new_prefix = self._get_sequence_prefix(
                        vals["code"], refund=False, type_note="debit"
                    )
                    journal.debit_note_sequence_id.write({"prefix": new_prefix})
            if vals.get("debit_note_sequence"):
                for journal in self.filtered(
                    lambda j: j.type in ("sale", "purchasex") and not j.debit_note_sequence_id
                ):
                    journal_vals = {
                        "name": journal.name,
                        "company_id": journal.company_id.id,
                        "code": journal.code,
                        "debit_note_sequence_number_next": vals.get(
                            "debit_note_sequence_number_next",
                            journal.debit_note_sequence_number_next,
                        ),
                    }
                    journal.debit_note_sequence_id = (
                        self.sudo()._create_sequence(journal_vals, type_note="debit").id
                    )
        result = super(AccountJournal, self).write(vals)

        # if vals.get('refund_sequence'):
        #     for journal in self.filtered(lambda j: j.type in ('sale', 'purchasex') and not j.refund_sequence_id):
        #         journal_vals = {
        #             'name': journal.name,
        #             'company_id': journal.company_id.id,
        #             'edi_code': journal.edi_code,
        #             'refund_sequence_number_next': vals.get('refund_sequence_number_next', journal.refund_sequence_number_next),
        #         }
        #         journal.refund_sequence_id = self.sudo()._create_sequence(journal_vals, type_note='credit').id

        return result

    @api.model
    def create(self, vals):

        # We just need to create the relevant sequences according to the chosen options
        # if vals.get('is_einvoicing', False):
        #     if not vals.get('sequence_id'):
        #         vals.update({'sequence_id': self.sudo()._create_sequence(vals).id})
        #     if vals.get('type') in ('sale', 'purchasex') and vals.get('refund_sequence') and not vals.get('refund_sequence_id'):
        #         vals.update({'refund_sequence_id': self.sudo()._create_sequence(vals, type_note='credit').id})
        if (
            vals.get("type") in ("sale", "purchasex")
            and vals.get("debit_note_sequence")
            and not vals.get("debit_note_sequence_id")
        ):
            vals.update(
                {"debit_note_sequence_id": self.sudo()._create_sequence(vals, type_note="debit").id}
            )
        journal = super(AccountJournal, self).create(vals)

        return journal

    @api.model
    def _get_sequence_prefix(self, code, refund=False, type_note=False):
        prefix = code.upper()
        if type_note == "credit" or refund:
            prefix = "C" + prefix
        if type_note == "debit":
            prefix = "D" + prefix
        return prefix  # + '/%(range_year)s/'

    @api.model
    def _create_sequence(self, vals, refund=False, type_note=False):
        """Create new no_gap entry sequence for every new Journal"""
        prefix = self._get_sequence_prefix(vals["code"], refund, type_note)
        seq_name = (
            (refund or type_note == "credit")
            and prefix + _(": Secuencia Rectificativa")
            or type_note == "debit"
            and prefix + _(": Secuencia Nota Débito")
            or vals["code"]
        )
        seq = {
            "name": "%s" % seq_name,
            "implementation": "no_gap",
            "prefix": prefix,
            "padding": 4,
            "number_increment": 1,
            "use_date_range": True,
        }
        if "company_id" in vals:
            seq["company_id"] = vals["company_id"]
        seq = self.env["ir.sequence"].create(seq)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = (
            (refund or type_note == "credit")
            and vals.get("refund_sequence_number_next", 1)
            or type_note == "debit"
            and vals.get("debit_note_sequence_number_next", 1)
            or vals.get("sequence_number_next", 1)
        )
        return seq

    def create_journal_sequence(self):
        if not self.sequence_id:
            seq = self.create_sequence(refund=False, type_note="")
            self.sequence_id = seq.id
        if self.refund_sequence and not self.refund_sequence_id:
            seq = self.create_sequence(refund=True, type_note="credit")
            self.refund_sequence_id = seq.id
        if self.debit_note_sequence and not self.debit_note_sequence_id:
            seq = self.create_sequence(refund=False, type_note="debit")
            self.debit_note_sequence_id = seq.id

    def create_sequence(self, refund=False, type_note=""):
        prefix = self._get_sequence_prefix(self.code, refund, type_note)
        seq_name = (
            (refund or type_note == "credit")
            and self.code + _(": Secuencia Rectificativa")
            or type_note == "debit"
            and self.code + _(": Secuencia Nota Débito")
            or self.code
        )
        seq = {
            "name": "%s" % seq_name,
            "implementation": "no_gap",
            "prefix": prefix,
            "padding": 4,
            "number_increment": 1,
            "use_date_range": True,
        }
        if self.company_id:
            seq["company_id"] = self.company_id.id
        seq = self.env["ir.sequence"].create(seq)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = (
            (refund or type_note == "credit")
            and (self.refund_sequence_number_next or 1)
            or type_note == "debit"
            and (self.debit_note_sequence_number_next or 1)
            or (self.sequence_number_next or 1)
        )
        return seq
