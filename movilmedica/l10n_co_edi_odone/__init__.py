from odoo import api, SUPERUSER_ID, tools
from . import controllers
from . import models
from . import wizards
from os.path import join, dirname, realpath
import logging

_logger = logging.getLogger(__name__)


# def _setup_tax_type(cr, registry):
def post_init_hook(cr, registry):
    # Código unspcs
    _load_unspsc_codes(cr, registry)
    _assign_codes_uom(cr, registry)

    # Asignar tipo de impuestos
    env = api.Environment(cr, SUPERUSER_ID, {})
    chart_template = env.ref("l10n_co.l10n_co_chart_template_generic", raise_if_not_found=False)
    if chart_template:
        companies = env["res.company"].search([("chart_template_id", "=", chart_template.id)])
        tax_templates = env["account.tax.template"].search(
            [
                ("chart_template_id", "=", chart_template.id),
                ("type_tax_use", "=", "sale"),
                ("l10n_co_edi_type", "!=", False),
            ]
        )
        xml_ids = tax_templates.get_external_id()
        for company in companies:
            for tax_template in tax_templates:
                module, xml_id = xml_ids.get(tax_template.id).split(".")
                tax = env.ref(
                    "{}.{}_{}".format(module, company.id, xml_id), raise_if_not_found=False
                )
                if tax:
                    tax.l10n_co_edi_type = tax_template.l10n_co_edi_type


# def post_init_hook(cr, registry):
#     _load_unspsc_codes(cr, registry)
#     _assign_codes_uom(cr, registry)


def uninstall_hook(cr, registry):
    cr.execute("DELETE FROM product_unspsc_code;")
    cr.execute("DELETE FROM ir_model_data WHERE model='product_unspsc_code';")


def _load_unspsc_codes(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv
    Even with the faster CSVs, it would take +30 seconds to load it with
    the regular ORM methods, while here, it is under 3 seconds
    """
    csv_path = join(dirname(realpath(__file__)), "data", "product.unspsc.code.csv")
    csv_file = open(csv_path, "rb")
    csv_file.readline()  # Read the header, so we avoid copying it to the db
    cr.copy_expert(
        """COPY product_unspsc_code (code, name, applies_to, active)
           FROM STDIN WITH DELIMITER '|'""",
        csv_file,
    )
    # Create xml_id, to allow make reference to this data
    cr.execute(
        """INSERT INTO ir_model_data
           (name, res_id, module, model, noupdate)
           SELECT concat('unspsc_code_', code), id, 'l10n_co_edi_odone', 'product.unspsc.code', 't'
           FROM product_unspsc_code"""
    )


def _assign_codes_uom(cr, registry):
    """Assign the codes in UoM of each data, this is here because the data is
    created in the last method"""
    tools.convert.convert_file(
        cr, "l10n_co_edi_odone", "data/uom_data.xml", None, mode="init", kind="data"
    )
