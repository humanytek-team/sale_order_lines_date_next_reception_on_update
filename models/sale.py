# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2017 Humanytek (<www.humanytek.com>).
#    Manuel Márquez <manuel@humanytek.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from datetime import datetime
from pytz import timezone

from openerp import api, models
from openerp.exceptions import UserError
from openerp.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _get_date_to_user_timezone(self, datetime_to_convert):
        """Returns the datetime received converted to a date set to
        timezone of user"""

        tz = self.env.context.get('tz', False)
        if not tz:
            tz = 'Mexico/General'

        datetime_now_with_tz = datetime.now(timezone(tz))
        utc_difference_timedelta = datetime_now_with_tz.utcoffset()
        datetime_to_convert = datetime.strptime(
            datetime_to_convert, '%Y-%m-%d %H:%M:%S')
        datetime_result = datetime_to_convert + utc_difference_timedelta
        date_result = datetime_result.strftime('%d-%m-%Y')

        return date_result

    @api.multi
    def button_dummy(self):

        super(SaleOrder, self).button_dummy()
        message = _('Not enough inventory!') + '\n'

        StockPicking = self.env['stock.picking']

        for line in self.order_line:
            if line.product_id.type == 'product':
                product_qty = self.env['product.uom']._compute_qty_obj(
                    line.product_uom,
                    line.product_uom_qty,
                    line.product_id.uom_id)

                if product_qty > (line.product_id.qty_available -
                    line.product_id.outgoing_qty) and product_qty > 0:

                    if line.product_id.incoming_qty > 0:

                        pickings = StockPicking.search([
                            ('picking_type_id.code', '=', 'incoming'),
                            ('state', '=', 'assigned'),
                            ('move_lines_related.product_id', '=',
                            line.product_id.id),
                        ], order='min_date')

                        if pickings:

                            date_next_receipt = self._get_date_to_user_timezone(
                                pickings[0].min_date)

                            message += '{0} \n'.format(line.product_id.display_name)
                            message += _('You plan to sell %.2f %s but the stock on hand is %.2f %s. The date of the next receipt is %s') % \
                                (
                                    line.product_uom_qty,
                                    line.product_uom.name,
                                    line.product_id.qty_available,
                                    line.product_id.uom_id.name,
                                    date_next_receipt
                                    )
                            message += '\n'

        if message != _('Not enough inventory! \n') + '\n':
            raise UserError(message)
