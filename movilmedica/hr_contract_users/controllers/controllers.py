# from odoo import http


# class HrContractUser(http.Controller):
#     @http.route('/hr_contract_users/hr_contract_users/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_contract_users/hr_contract_users/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_contract_users.listing', {
#             'root': '/hr_contract_users/hr_contract_users',
#             'objects': http.request.env['hr_contract_users.hr_contract_user's].search([]),
#         })

#     @http.route('/hr_contract_users/hr_contract_users/objects/<model("hr_contract_users.hr_contract_users"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_contract_users.object', {
#             'object': obj
#         })
