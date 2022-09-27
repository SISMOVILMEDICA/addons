from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    # l10n_co_edi_description_code_credit = fields.Selection(DESCRIPTION_CREDIT_CODE,
    #                                                        string="Concepto", help="Colombian code for Credit Notes")
    l10n_co_edi_discrepancy_response_id = fields.Many2one(
        "l10n_co_edi.discrepancy.response",
        string="Concepto de corrección",
        domain=[("type", "=", "credit")],
    )

    def reverse_moves(self):
        action = super(AccountMoveReversal, self).reverse_moves()
        for refund in self.new_move_ids:
            refund.l10n_co_edi_discrepancy_response_id = self.l10n_co_edi_discrepancy_response_id
            refund.type_note = "credit"
            refund._onchange_type()
        return action

    # def _prepare_default_reversal(self, move):
    #     """ Set the document refund_type as credit note """
    #     res = super()._prepare_default_reversal(move)
    #     if move.move_type and move.move_type in ('out_invoice','out_refund'):
    #         res.update({'refund_type': 'credit',
    #                     'discrepancy_response_code_id': self.l10n_co_edi_discrepancy_response_id.id or False,
    #                     'l10n_co_edi_payment_option_id': move.l10n_co_edi_payment_option_id.id or False,
    #         })
    #     return res
