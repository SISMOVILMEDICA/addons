from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    vals = {
        "voucher_reconcile_amount": 1000,
    }
    env["res.config.settings"].create(vals).set_values()
