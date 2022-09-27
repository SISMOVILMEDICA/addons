from odoo import _, api, fields, models


class ProjectTaskProduct(models.Model):
    _name = "project.task.product"
    _description = "Productos a facturar del servicio"

    task_id = fields.Many2one(comodel_name="project.task", string="Servicio")
    product_id = fields.Many2one(comodel_name="product.product", string="Producto")
    price = fields.Float(string="Precio")
    quantity = fields.Integer(string="Cantidad")
