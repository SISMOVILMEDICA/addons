{
    "name": "Contract User",
    "summary": "Contract User",
    "description": "Contract User",
    "author": "Odone",
    "website": "https://www.odone.com.co",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Human Resources/Contracts",
    "version": "14.1",
    # any module necessary for this one to work correctly
    "depends": ["hr_contract"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/hr_specialty_data.xml",
        "views/hr_allergy_view.xml",
        "views/hr_document_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_illness_view.xml",
        "views/hr_specialty_view.xml",
        "views/templates.xml",
        "report/odone_nomina_report.xml",
        "views/odone_contrato_ops.xml",
        "views/acta_confidencialidad.xml",
        "views/odone_registro_induccion.xml",
        "views/oferta_contrato_ops.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
