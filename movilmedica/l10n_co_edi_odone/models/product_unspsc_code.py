from odoo import api, fields, models
from odoo.osv import expression


class ProductCode(models.Model):
    """Product and UoM codes defined by UNSPSC
    Used by Mexico, Peru and Colombia localizations
    """

    _name = "product.unspsc.code"
    _description = "Product and UOM Codes from UNSPSC"

    code = fields.Char("Code", required=True)
    name = fields.Char("Name", required=True)
    applies_to = fields.Selection(
        [
            ("product", "Product"),
            ("uom", "UoM"),
        ],
        required=True,
        help="Indicate if this code could be used in products or in UoM",
    )
    active = fields.Boolean()

    def name_get(self):
        result = []
        for prod in self:
            result.append((prod.id, "{} {}".format(prod.code, prod.name or "")))
        return result

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        if operator == "ilike" and not (name or "").strip():
            domain = []
        else:
            domain = ["|", ("name", "ilike", name), ("code", "ilike", name)]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )
