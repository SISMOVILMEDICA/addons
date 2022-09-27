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

import logging
import re

# Extended Partner Module
from odoo import api, exceptions, fields, models
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class PartnerInfoExtended(models.Model):
    _inherit = "res.partner"

    # Adding new name fields
    x_name1 = fields.Char("First Name")
    x_name2 = fields.Char("Second Name")
    x_lastname1 = fields.Char("Last Name")
    x_lastname2 = fields.Char("Second Last Name")

    # CIIU - Clasificación Internacional Industrial Uniforme
    ciiu = fields.Many2one("res.ciiu", "ISIC Activity")

    @api.onchange("x_name1", "x_name2", "x_lastname1", "x_lastname2")
    def _concat_name(self):
        """
        This function concatenates the four name fields in order to be able to
        search for the entire name. On the other hand the original name field
        should not be editable anymore as the new name fields should fill it up
        automatically.
        @return: void
        """
        # Avoiding that "False" will be written into the name field
        if not self.x_name1:
            self.x_name1 = ""

        if not self.x_name2:
            self.x_name2 = ""

        if not self.x_lastname1:
            self.x_lastname1 = ""

        if not self.x_lastname2:
            self.x_lastname2 = ""

        # Collecting all names in a field that will be concatenated
        nameList = [
            self.x_name1.encode(encoding="utf-8").strip(),
            self.x_name2.encode(encoding="utf-8").strip(),
            self.x_lastname1.encode(encoding="utf-8").strip(),
            self.x_lastname2.encode(encoding="utf-8").strip(),
        ]

        formatedList = []

        if self.company_type == "company":
            self.x_name1 = False
            self.x_name2 = False
            self.x_lastname1 = False
            self.x_lastname2 = False
        else:
            for item in nameList:
                if item != b"":
                    formatedList.append(item.decode("UTF-8"))
                self.name = " ".join(formatedList).title()

    # @api.onchange('name')
    # def on_change_name(self):
    #     """
    #     The name field gets concatenated by the four name fields.
    #     If a user enters a value anyway, the value will be deleted except first
    #     name has no value. Reason: In certain forms of odoo it is still
    #     possible to add value to the original name field. Therefore we have to
    #     ensure that this field can receive values unless we offer the four name
    #     fields.
    #     @return: void
    #     """
    #     if self.x_name1 is not False:
    #         if len(self.x_name1) > 0:
    #             self._concat_name()
    #     if self.companyName is not False:
    #         if len(self.companyName) > 0:
    #             self._concat_name()
