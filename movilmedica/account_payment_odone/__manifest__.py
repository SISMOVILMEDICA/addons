{
    "name": "Online Billing",
    "summary": "Send Invoices and Track Vouchers",
    "description": "Invoicing & Vouchers by Accounting Voucher & Receipts",
    "author": "Odone",
    "contributors": [
        "Juan Pablo Arcos juanparmer@gmail.com",
    ],
    "website": "https://www.odone.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Accounting & Finance",
    "version": "14.1",
    # any module necessary for this one to work correctly
    "depends": [
        "account_payment",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_security.xml",
        "security/res_groups_security.xml",
        "data/ir_sequence_data.xml",
        "views/account_journal_view.xml",
        "views/account_payment_view.xml",
        "views/account_voucher_line_view.xml",
        "views/account_voucher_view.xml",
        "views/res_config_settings_view.xml",
        "wizard/account_voucher_wizard_view.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
    # hook
    "post_init_hook": "post_init_hook",
}
