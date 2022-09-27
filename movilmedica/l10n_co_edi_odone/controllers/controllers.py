# from odoo import http


# class DianEfact(http.Controller):
#     @http.route('/dian_efact/dian_efact/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dian_efact/dian_efact/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dian_efact.listing', {
#             'root': '/dian_efact/dian_efact',
#             'objects': http.request.env['dian_efact.dian_efact'].search([]),
#         })

#     @http.route('/dian_efact/dian_efact/objects/<model("dian_efact.dian_efact"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dian_efact.object', {
#             'object': obj
#         })
