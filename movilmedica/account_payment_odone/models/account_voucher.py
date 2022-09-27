import num2words

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountVoucher(models.Model):
    _name = "account.voucher"
    _description = "Accounting Voucher"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    def _default_journal_id(self):
        domain = [("type", "in", ("cash", "bank"))]
        return self.env["account.journal"].search(domain, limit=1)

    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Destination Account",
        readonly=False,
        domain="[('user_type_id.type', 'in', ('receivable', 'payable')), ('company_id', '=', company_id)]",
        check_company=True,
    )

    amount = fields.Monetary(string="Amount", tracking=True)
    amount_active = fields.Monetary(string="Amount Active", compute="_compute_amount", store=True)
    amount_passive = fields.Monetary(string="Amount Passive", compute="_compute_amount", store=True)
    amount_reconcile = fields.Monetary(
        string="Amount Reconcile", compute="_compute_amount", store=True
    )
    amount_voucher = fields.Monetary(
        string="Amount Voucher", compute="_compute_amount_voucher", store=True
    )

    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", default=lambda self: self.env.company
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Company Currency",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        readonly=False,
        default=lambda self: self.env.company.currency_id,
        help="The voucher's currency.",
    )

    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        required=True,
        copy=False,
    )

    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Journal", required=True, default=_default_journal_id
    )

    line_active_ids = fields.One2many(
        comodel_name="account.voucher.line",
        inverse_name="voucher_active_id",
        string="Active Lines",
        copy=False,
    )
    line_passive_ids = fields.One2many(
        comodel_name="account.voucher.line",
        inverse_name="voucher_passive_id",
        string="Passive Lines",
        copy=False,
    )
    line_reconcile_ids = fields.One2many(
        comodel_name="account.voucher.line",
        inverse_name="voucher_reconcile_id",
        string="Reconcile Lines",
        copy=False,
    )

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
        readonly=True,
        ondelete="cascade",
        check_company=True,
        copy=False,
    )

    name = fields.Char(string="Name", default=_("New"))

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="restrict",
        domain="['|', ('parent_id','=', False), ('is_company','=', True)]",
        check_company=True,
        tracking=True,
        required=True,
    )
    partner_type = fields.Selection(
        selection=[("customer", "Customer"), ("supplier", "Supplier")],
        default="customer",
        required=True,
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("cancel", "Cancelled"), ("posted", "Posted")],
        string="Status",
        readonly=True,
        tracking=True,
        copy=False,
        default="draft",
    )

    voucher_date = fields.Date(
        string="Voucher Date",
        default=fields.Date.context_today,
        copy=False,
    )
    voucher_reference = fields.Char(
        string="Voucher Reference",
        copy=False,
        help="Reference of the document used to issue this voucher. Eg. check number, file name, etc.",
    )
    voucher_type = fields.Selection(
        selection=[("voucher", "Voucher"), ("advance", "Advance"), ("cross", "Cross")],
        string="Voucher Type",
        default="voucher",
        required=True,
        tracking=True,
    )

    writeoff_amount = fields.Monetary(
        compute="_compute_writeoff",
        string="Difference Amount",
        store=True,
        help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines.",
    )
    writeoff_comment = fields.Char(string="Counterpart Comment", default=_("Write-Off"))
    writeoff_option = fields.Selection(
        selection=[
            ("without_writeoff", "Keep Open"),
            ("with_writeoff", "Reconcile Voucher Balance"),
        ],
        string="Voucher Difference",
        required=True,
        default="without_writeoff",
        help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the voucher(s)",
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            values = self._prepare_partner_id()
            self.update(values)

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        if self.journal_id:
            currency_id = self.journal_id.currency_id or self.company_id.currency_id
            self.update({"currency_id": currency_id.id})

    @api.onchange("voucher_type")
    def _onchange_voucher_type(self):
        if self.voucher_type == "advance":
            self.update(
                {
                    "line_active_ids": [],
                    "line_passive_ids": [],
                    "line_reconcile_ids": [],
                    "writeoff_option": "without_writeoff",
                }
            )
        if self.voucher_type == "cross":
            self.update({"amount": 0.0, "writeoff_option": "with_writeoff"})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self.env["ir.sequence"].next_by_code("account.voucher") or _("New")
        return super(AccountVoucher, self).create(vals_list)

    @api.depends("line_active_ids.amount", "line_passive_ids.amount", "line_reconcile_ids.amount")
    def _compute_amount(self):
        for voucher in self:
            amount_active = sum(voucher.line_active_ids.mapped("amount"))
            amount_passive = sum(voucher.line_passive_ids.mapped("amount"))
            amount_reconcile = sum(voucher.line_reconcile_ids.mapped("amount"))
            voucher.update(
                {
                    "amount_active": amount_active,
                    "amount_passive": amount_passive,
                    "amount_reconcile": amount_reconcile,
                }
            )

    @api.depends("voucher_type", "amount", "amount_passive")
    def _compute_amount_voucher(self):
        for voucher in self:
            if voucher.voucher_type != "cross":
                amount_voucher = voucher.amount
            else:
                amount_voucher = voucher.amount_passive
            voucher.update({"amount_voucher": amount_voucher})

    @api.depends("amount", "amount_active", "amount_passive")
    def _compute_writeoff(self):
        for voucher in self:
            amount_active = voucher.amount + voucher.amount_active
            amount_passive = voucher.amount_passive
            writeoff_amount = amount_active - amount_passive
            voucher.update({"writeoff_amount": writeoff_amount})

    def _prepare_partner_id(self):
        self.ensure_one()
        values = {}
        values.update(self._prepare_account_id())
        return values

    def _prepare_account_id(self):
        self.ensure_one()
        partner_id = self.partner_id
        receivable_id = partner_id.property_account_receivable_id
        payable_id = partner_id.property_account_payable_id
        account_id = payable_id if self.partner_type == "supplier" else receivable_id
        return {"account_id": account_id.id}

    def compute_line_ids(self):
        for voucher in self:
            voucher._compute_line_ids()

    def _compute_line_ids(self):
        self.ensure_one()
        self.line_active_ids.unlink()
        self.line_passive_ids.unlink()
        line_ids = self._prepare_line_ids()
        self.write(line_ids)

    def _prepare_line_ids(self):
        self.ensure_one()

        value = {"line_active_ids": [], "line_passive_ids": []}

        domain = [
            ("parent_state", "=", "posted"),
            ("reconciled", "=", False),
            ("partner_id", "=", self.partner_id.id),
            ("account_id.internal_type", "in", ("payable", "receivable")),
        ]
        # if self.voucher_type == 'voucher':
        #     domain.append(('account_id', '=', self.account_id.id))
        if self._context.get("line_ids"):
            domain.append(("id", "in", self._context.get("line_ids")))
        account_move_lines = self.env["account.move.line"].search(domain, order="date_maturity")

        amount_credit = sum(
            line.currency_id._convert(
                line.credit or 0.0, self.currency_id, self.company_id, line.date
            )
            for line in account_move_lines
        )
        amount_debit = sum(
            line.currency_id._convert(
                line.debit or 0.0, self.currency_id, self.company_id, line.date
            )
            for line in account_move_lines
        )
        amount_active = amount_credit if self.partner_type == "customer" else amount_debit
        remaining_amount = self.amount + amount_active

        for move_line in account_move_lines:
            if move_line.currency_id and move_line.currency_id.id == self.currency_id.id:
                amount_original = abs(move_line.amount_currency)
                amount_unreconciled = abs(move_line.amount_residual_currency)
            else:
                amount_original = self.company_currency_id._convert(
                    move_line.debit or move_line.credit,
                    self.currency_id,
                    self.company_id,
                    self.date,
                )
                amount_unreconciled = self.company_currency_id._convert(
                    abs(move_line.amount_residual), self.currency_id, self.company_id, self.date
                )

            if not amount_unreconciled:
                continue

            line_debit = amount_unreconciled if move_line.debit else 0.0
            line_credit = amount_unreconciled if move_line.credit else 0.0
            line_active = line_debit if self.partner_type == "supplier" else line_credit

            amount = min(remaining_amount, amount_unreconciled)

            if line_active > 0:
                amount = amount_unreconciled

            line = {
                "account_id": move_line.account_id.id,
                "amount": amount if amount >= 0 else amount_unreconciled,
                "amount_original": amount_original,
                "amount_unreconciled": amount_unreconciled,
                "currency_id": self.currency_id.id,
                "line_type": move_line.credit and "credit" or "debit",
                "move_line_id": move_line.id,
                "name": move_line.move_id.name,
                "partner_id": self.partner_id.id,
            }

            line_debit = line["amount"] if line["line_type"] == "debit" else 0.0
            line_credit = line["amount"] if line["line_type"] == "credit" else 0.0
            line_passive = line_debit if self.partner_type == "customer" else line_credit

            remaining_amount -= line_passive

            if line["amount_unreconciled"] == line["amount"]:
                line["reconcile"] = True

            if line_active > 0:
                value["line_active_ids"].append((0, 0, line))
            else:
                value["line_passive_ids"].append((0, 0, line))
        return value

    def button_line_unlink(self):
        for voucher in self.filtered(lambda v: v.state == "draft"):
            voucher._button_line_unlink()

    def _button_line_unlink(self):
        self.ensure_one()
        lines = self.line_passive_ids.filtered(lambda l: not l.amount)
        line_passive_ids = [(2, line.id, 0) for line in lines]
        lines = self.line_active_ids.filtered(lambda l: not l.amount)
        line_active_ids = [(2, line.id, 0) for line in lines]
        self.write(
            {
                "line_passive_ids": line_passive_ids,
                "line_active_ids": line_active_ids,
            }
        )

    def button_line_amount(self):
        for voucher in self.filtered(lambda v: v.state == "draft"):
            voucher._button_line_amount()

    def _button_line_amount(self):
        self.ensure_one()
        lines = self.line_passive_ids + self.line_active_ids
        lines.write({"amount": 0.0, "reconcile": False})

    def action_post(self):
        for voucher in self:
            voucher._action_post()
            voucher._action_reconcile()
        return True

    def _action_post(self):
        self.ensure_one()
        self._check_post()
        move_id = self.env["account.move"].create(self._prepare_move_id())
        move_id.action_post()
        self.write(
            {
                "move_id": move_id,
                "state": "posted",
            }
        )

    def _check_post(self):
        self.ensure_one()
        if self.writeoff_amount and self.writeoff_option != "without_writeoff":
            if self.writeoff_amount - self.amount_reconcile != 0.0:
                if self.voucher_type != "cross":
                    raise ValidationError(_("Cannot confirm a voucher with differences."))
                else:
                    if (
                        abs(self.writeoff_amount - self.amount_reconcile)
                        > self.company_id.voucher_reconcile_amount
                    ):
                        raise ValidationError(_("Cannot confirm a voucher with differences."))
                    else:
                        self.write(self._prepare_reconcile_id())
        return True

    def _action_reconcile(self):
        self.ensure_one()
        if not self.move_id:
            return False
        for line in self.move_id.line_ids.filtered(lambda l: l.voucher_line_id):
            (line | line.voucher_line_id).with_context(move_reverse_cancel="cancel").reconcile()

    def _prepare_move_id(self):
        return {
            "move_type": "entry",
            "partner_id": self.partner_id.id,
            "journal_id": self.journal_id.id,
            "currency_id": self.currency_id.id,
            "date": self.date,
            "ref": self.voucher_reference,
            "line_ids": self._prepare_move_line_id(),
        }

    def _prepare_move_line_id(self):
        line_ids = []
        sign = self.partner_type == "customer" and 1 or -1
        if self.amount:
            amount = self.amount * sign
            amount_currency = amount
            amount = self.currency_id._convert(
                amount, self.company_currency_id, self.company_id, self.date
            )
            line = {
                "name": self.name or "/",
                "debit": amount if amount > 0 else 0.0,
                "credit": -amount if amount < 0 else 0.0,
                "account_id": self.journal_id.default_account_id.id,
                "partner_id": self.partner_id.id,
                "currency_id": self.currency_id.id,
                "amount_currency": amount_currency,
                "date": self.date,
            }
            line_ids.append((0, 0, line))
        if self.voucher_type != "advance":
            for line in (self.line_passive_ids | self.line_active_ids).filtered(lambda l: l.amount):
                debit = line.move_line_id.credit and line.amount or 0.0
                credit = line.move_line_id.debit and line.amount or 0.0
                amount_currency = debit - credit
                debit = self.currency_id._convert(
                    debit, self.company_currency_id, self.company_id, self.date
                )
                credit = self.currency_id._convert(
                    credit, self.company_currency_id, self.company_id, self.date
                )
                line = {
                    "name": self.name or "/",
                    "debit": debit,
                    "credit": credit,
                    "account_id": line.move_line_id.account_id.id,
                    "partner_id": self.partner_id.id,
                    "currency_id": line.currency_id.id,
                    "amount_currency": amount_currency,
                    "date": self.date,
                    "voucher_line_id": line.move_line_id.id,
                }
                line_ids.append((0, 0, line))
        if self.writeoff_amount:
            writeoff_amount = self.writeoff_amount * sign
            if self.writeoff_option == "without_writeoff":
                amount_currency = writeoff_amount
                writeoff_amount = self.currency_id._convert(
                    writeoff_amount, self.company_currency_id, self.company_id, self.date
                )
                line = {
                    "name": self.name or _("Write-Off"),
                    "debit": -writeoff_amount if writeoff_amount < 0 else 0.0,
                    "credit": writeoff_amount if writeoff_amount > 0 else 0.0,
                    "account_id": self.account_id.id,
                    "partner_id": self.partner_id.id,
                    "currency_id": self.currency_id.id,
                    "amount_currency": amount_currency,
                    "date": self.date,
                }
                line_ids.append((0, 0, line))
            else:
                for line in self.line_reconcile_ids.filtered(lambda l: l.amount):
                    amount = line.amount * sign
                    amount_currency = amount
                    amount = self.currency_id._convert(
                        amount, self.company_currency_id, self.company_id, self.date
                    )
                    line = {
                        "name": line.comment or _("Write-Off"),
                        "debit": -amount if amount < 0 else 0.0,
                        "credit": amount if amount > 0 else 0.0,
                        "account_id": line.account_id.id,
                        "partner_id": self.partner_id.id,
                        "currency_id": self.currency_id.id,
                        "amount_currency": amount_currency,
                        "date": self.date,
                        "analytic_account_id": line.analytic_id.id,
                        "analytic_tag_ids": [(6, id, line.analytic_tag_ids.ids)],
                    }
                    line_ids.append((0, 0, line))
        return line_ids

    def _prepare_reconcile_id(self):
        sign = self.partner_type == "customer" and 1 or -1
        accounts = self.journal_id._prepare_voucher_data()
        amount = self.writeoff_amount * sign
        account_id = accounts.get("account_debit") if amount > 0 else accounts.get("account_credit")
        value = {
            "account_id": account_id.id,
            "amount": amount,
            "currency_id": self.currency_id.id,
            "name": self.name,
            "partner_id": self.partner_id.id,
        }
        return {"line_reconcile_ids": [(0, 0, value)]}

    def action_draft(self):
        self.write({"state": "draft", "move_id": False})
        return True

    def action_cancel(self):
        for voucher in self.filtered(lambda v: v.move_id):
            voucher.move_id.button_draft()
            voucher.move_id.button_cancel()
        self.write({"state": "cancel"})
        return True


class AccountVoucherLine(models.Model):
    _name = "account.voucher.line"
    _description = "Voucher Lines"

    account_id = fields.Many2one(comodel_name="account.account", string="Account", required=True)

    amount = fields.Monetary(string="Amount")
    amount_original = fields.Monetary(string="Original Amount")
    amount_unreconciled = fields.Monetary(string="Open Balance")
    amount_untax = fields.Monetary(string="Untax Amount")

    analytic_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
    )
    analytic_tag_ids = fields.Many2many(comodel_name="account.analytic.tag", string="Analytic Tags")

    comment = fields.Char(string="Counterpart Comment", default=_("Write-Off"))

    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", default=lambda self: self.env.company
    )

    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency")

    date_original = fields.Date(related="move_line_id.date")
    date_due = fields.Date(related="move_line_id.date_maturity")

    line_type = fields.Selection(
        selection=[("debit", "Debit"), ("credit", "Credit")], string="Debit / Credit"
    )

    move_line_id = fields.Many2one(
        comodel_name="account.move.line", string="Journal Item", copy=False
    )

    name = fields.Char(string="Description")

    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")

    reconcile = fields.Boolean(string="Full Reconcile", default=False)

    voucher_active_id = fields.Many2one(
        comodel_name="account.voucher", string="Active", ondelete="cascade"
    )
    voucher_passive_id = fields.Many2one(
        comodel_name="account.voucher", string="Passive", ondelete="cascade"
    )
    voucher_reconcile_id = fields.Many2one(
        comodel_name="account.voucher", string="Reconcile", ondelete="cascade"
    )

    @api.onchange("reconcile")
    def _onchange_reconcile(self):
        if self.reconcile:
            self.update({"amount": self.amount_unreconciled})

    @api.onchange("amount")
    def _onchange_amount(self):
        if self.amount:
            self.update({"reconcile": self.amount == self.amount_unreconciled})

    @api.onchange("move_line_id")
    def _onchange_move_line_id(self):
        if self.move_line_id:
            self.update(
                {
                    "account_id": self.move_line_id.account_id.id,
                    "line_type": self.move_line_id.credit and "credit" or "debit",
                }
            )
