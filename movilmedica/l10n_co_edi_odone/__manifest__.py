{
    "name": "Facturación Electrónica Colombiana",
    "summary": """
        -Facturación electrónica Colombiana directa a la DIAN.""",
    "description": """
        -Facturación electrónica Colombiana directa a la DIAN.
    """,
    "author": "Odone",
    "website": "https://www.odone.com.co",
    "category": "Accounting/Localizations/EDI",
    "version": "0.1",
    "depends": [
        "account",
        "l10n_co",
        "l10n_latam_base",
        "uom",
        "account_debit_note",
        "od_journal_sequence",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account.tax.group.csv",
        "data/l10n_co_edi.type_code.csv",
        "data/l10n_co_edi.tax.type.csv",
        "data/account.tax.template.csv",
        "data/res_partner_data.xml",
        "data/res.city.csv",
        "data/res.country.state.csv",
        "data/res_country_data.xml",
        "data/l10n_latam.identification.type.csv",
        "data/l10n_co_edi.uom.code.csv",
        "data/l10n_co_edi_discrepancy_response_data.xml",
        "data/l10n_co_edi.payment.option.csv",
        # 'data/product.unspsc.code.csv',  # Se agregan por pyhton
        # 'data/uom_data.xml',
        "views/res_country_state_views.xml",
        "views/res_city_views.xml",
        "views/res_partner_views.xml",
        "views/type_code_views.xml",
        "views/identification_type_views.xml",
        "views/tax_type_views.xml",
        "views/account_tax_views.xml",
        "views/product_uom_views.xml",
        "views/product_template_views.xml",
        "views/l10n_co_edi_discrepancy_response_views.xml",
        "views/account_move_views.xml",
        "views/ir_sequence_views.xml",
        "views/account_journal_views.xml",
        "views/res_company_views.xml",
        "views/l10n_co_edi_email_templates.xml",
        "wizards/account_move_reversal_views.xml",
        "wizards/account_debit_note_views.xml",
        "reports/account_move_reports.xml",
        "reports/account_move_templates.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "external_dependencies": {
        "python": [
            "unidecode",
            "xmlsig",
            "jinja2",
            "OpenSSL",
            "xades",
            "qrcode",
        ],
    },
}
