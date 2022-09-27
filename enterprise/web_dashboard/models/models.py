from lxml.builder import E

from odoo import api, models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _get_default_dashboard_view(self):
        """Generates a default dashboard view containing default sub graph and
        pivot views.

        :returns: a dashboard view as an lxml document
        :rtype: etree._Element
        """
        dashboard = E.dashboard()
        dashboard.append(E.view(type="graph"))
        dashboard.append(E.view(type="pivot"))
        return dashboard
