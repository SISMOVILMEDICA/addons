# from odoo import http


# class IndustryFsmExtended(http.Controller):
#     @http.route('/industry_fsm_movilmedica/industry_fsm_movilmedica/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/industry_fsm_movilmedica/industry_fsm_movilmedica/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('industry_fsm_movilmedica.listing', {
#             'root': '/industry_fsm_movilmedica/industry_fsm_movilmedica',
#             'objects': http.request.env['industry_fsm_movilmedica.industry_fsm_movilmedica'].search([]),
#         })

#     @http.route('/industry_fsm_movilmedica/industry_fsm_movilmedica/objects/<model("industry_fsm_movilmedica.industry_fsm_movilmedica"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('industry_fsm_movilmedica.object', {
#             'object': obj
#         })
