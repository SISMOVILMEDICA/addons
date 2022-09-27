###############################################################################
#                                                                             #
# Copyright (C) 2016  Dominic Krimmer                                         #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from odoo import api, fields, models
from odoo.osv import expression


class IndustrialClassification(models.Model):
    _name = "res.ciiu"  # res.co.ciiu
    _description = "ISIC List"

    name = fields.Char("Name", required=True)
    code = fields.Char("Code", required=True)
    description = fields.Char("Description")

    type = fields.Char(string="Type", store=True, compute="_compute_set_type")

    has_parent = fields.Boolean("Has Parent?", default=True)
    parent = fields.Many2one("res.ciiu", "Parent")

    has_division = fields.Boolean("Has Division?")
    division = fields.Many2one("res.ciiu", "Division")

    has_section = fields.Boolean("Has Section?")
    section = fields.Many2one("res.ciiu", "Section")

    hierarchy = fields.Selection(
        [("1", "Has Parent?"), ("2", "Has Division?"), ("3", "Has Section?")], "Hierarchy"
    )

    def name_get(self):
        result = []
        for res in self:
            name = "[{}] {}".format(res.code, res.name)
            result.append((res.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("name", operator, name), ("code", operator, name)]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )

    # @api.multi
    @api.depends("has_parent")
    def _compute_set_type(self):
        """
        Section, Division and Parent should be visually separated in the tree
        view. Therefore we tag them accordingly as 'view' or 'other'
        @return: void
        """
        for rec in self:
            # Child
            if rec.has_parent is True:
                if rec.division is True:
                    rec.type = "view"
                elif rec.section is True:
                    rec.type = "view"
                else:
                    rec.type = "other"
            # Division
            else:
                rec.type = "view"
