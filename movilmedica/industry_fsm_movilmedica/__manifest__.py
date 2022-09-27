{
    "name": "Field Service Movilmedica",
    "summary": "Field Service",
    "description": "Field Service",
    "author": "Odone",
    "website": "https://www.odone.com.co",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Services/Field Service",
    "version": "1",
    # any module necessary for this one to work correctly
    "depends": [
        "contacts",
        "industry_fsm",
        "hr_contract_users",
        "clinic_history",
        "mail",
        "custom_fields",
    ],
    # always loaded
    "data": [
        "data/ir_sequence_data.xml",
        "data/project_task_type_data.xml",
        "data/mail_data.xml",
        "security/ir.model.access.csv",
        "views/calendar_event_view.xml",
        "views/clinic_history_view.xml",
        "views/customer_contract_view.xml",
        "views/hr_specialty_view.xml",
        "views/project_project_view.xml",
        "views/project_task_view.xml",
        "views/res_locality_view.xml",
        "views/res_neighborhood_view.xml",
        "views/res_partner_view.xml",
        "views/project_task_product.xml",
        "views/project_task_product_extra.xml",
        "views/customer_contract_cups.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
