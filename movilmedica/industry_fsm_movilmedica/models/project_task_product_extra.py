from odoo import _, fields, models


class ProjectTaskProductExtra(models.Model):
    _name = "project.task.product.extra"
    _description = "Productos extra a facturar del servicio"

    task_id = fields.Many2one(comodel_name="project.task", string="Servicio")
    product_id = fields.Many2one(comodel_name="product.product", string="Producto")
    price = fields.Float(string="Precio", related="product_id.lst_price", readonly=True)
    quantity = fields.Integer(string="Cantidad", default=1)
