# from odoo import http


# class AccountIps(http.Controller):
#     @http.route('/account_ips/account_ips/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_ips/account_ips/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_ips.listing', {
#             'root': '/account_ips/account_ips',
#             'objects': http.request.env['account_ips.account_ips'].search([]),
#         })

#     @http.route('/account_ips/account_ips/objects/<model("account_ips.account_ips"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_ips.object', {
#             'object': obj
#         })
