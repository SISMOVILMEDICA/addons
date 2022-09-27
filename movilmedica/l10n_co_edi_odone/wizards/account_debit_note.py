from odoo import fields, models


class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"

    # l10n_co_edi_description_code_debit = fields.Selection(DESCRIPTION_DEBIT_CODE,
    #                                                       string="Concepto Nota de Débito", help="Colombian code for Debit Notes")
    l10n_co_edi_discrepancy_response_id = fields.Many2one(
        "l10n_co_edi.discrepancy.response",
        string="Concepto de corrección",
        domain=[("type", "=", "debit")],
    )

    def create_debit(self):
        action = super(AccountDebitNote, self).create_debit()
        if action.get("res_id"):
            debit_move = self.env["account.move"].browse(action["res_id"])
            debit_move.l10n_co_edi_discrepancy_response_id = (
                self.l10n_co_edi_discrepancy_response_id
            )
            debit_move.type_note = "debit"
            debit_move.l10n_co_edi_operation_type = "30"
            debit_move.invoice_payment_term_id = (
                debit_move.debit_origin_id.invoice_payment_term_id.id or False
            )
            debit_move._onchange_recompute_dynamic_lines()
        return action
