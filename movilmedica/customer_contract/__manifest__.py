{
    "name": "Contratos de clientes",
    "summary": """Contratos de clientes""",
    "description": """
Contratos de clientes
---------------------
Este modulo permite el control de diversos contratos para un mismo cliente, gestionando:
    * Otros si.
    * Pólizas.
    * CUPS.
    """,
    "author": "Odone",
    "website": "https://www.odone.com.co/",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Contratos",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["contacts", "product"],
    # always loaded
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/customer_contract_data.xml",
        "wizard/views/customer_contract_create_annex.xml",
        "wizard/views/customer_contract_delete_annex.xml",
        "wizard/views/customer_contract_create_report_budget.xml",
        "wizard/views/customer_contract_delete_report_budget.xml",
        "views/res_partner.xml",
        "views/customer_contract.xml",
        "views/customer_contract_report_budget.xml",
        "views/customer_contract_annex.xml",
        "views/customer_contract_diagnostic_view.xml",
        "views/customer_contract_policy.xml",
        "views/customer_contract_cups.xml",
        "views/customer_contract_cups_detail.xml",
        "views/product_template.xml",
        "views/product_product.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
