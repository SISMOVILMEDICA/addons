# from odoo import http


# class AccountVoucherExtended(http.Controller):
#     @http.route('/account_payment_odone/account_payment_odone/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_payment_odone/account_payment_odone/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_payment_odone.listing', {
#             'root': '/account_payment_odone/account_payment_odone',
#             'objects': http.request.env['account_payment_odone.account_payment_odone'].search([]),
#         })

#     @http.route('/account_payment_odone/account_payment_odone/objects/<model("account_payment_odone.account_payment_odone"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_payment_odone.object', {
#             'object': obj
#         })
