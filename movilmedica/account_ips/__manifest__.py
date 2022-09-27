{
    "name": "Account IPS",
    "summary": """
        Ajustes de facturación para IPS""",
    "description": """
        Ajustes de facturación para IPS
    """,
    "author": "Odone",
    "website": "https://www.odone.com.co",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "accounting",
    "version": "14.1",
    # any module necessary for this one to work correctly
    "depends": [
        # 'account',
        "l10n_co_edi_odone",
    ],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/account_move_views.xml",
        "views/res_company_views.xml",
        "reports/account_move_reports.xml",
        "reports/account_move_templates.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        # 'demo/demo.xml',
    ],
}
