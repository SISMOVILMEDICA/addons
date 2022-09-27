from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    product_template_ids = fields.Many2many(
        comodel_name="product.template",
        compute="_compute_product_template_ids",
    )

    @api.depends("item_ids.product_tmpl_id")
    def _compute_product_template_ids(self):
        for pricelist in self:
            pricelist.product_template_ids = pricelist.item_ids.product_tmpl_id
