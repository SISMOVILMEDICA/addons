{
    "name": "Clinic History",
    "summary": "Clinic History",
    "description": "Clinic History",
    "author": "Odone",
    "website": "https://www.odone.com.co",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Services/Field Service",
    "version": "1",
    # any module necessary for this one to work correctly
    "depends": [
        "project",
        "industry_fsm",
        "cie_rips",
        "customer_contract",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/cie_rips.xml",
        "views/clinic_history_recommendation_view.xml",
        "views/clinic_history_view.xml",
        # "report/historias_clinicas_reports.xml",
        'report/clinic_historical_report.xml',
        "views/historia_clinica_general.xml",
    ],
}
