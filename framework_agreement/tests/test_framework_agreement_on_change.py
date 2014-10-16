# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013, 2014 Camptocamp SA
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
##############################################################################
from datetime import timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.tests.common as test_common
from openerp import exceptions
from .common import BaseAgreementTestMixin


class TestAgreementOnChange(test_common.TransactionCase,
                            BaseAgreementTestMixin):
    """Test observer on change and purchase order on chnage"""

    def setUp(self):
        """ Create a default agreement
        with 3 price line
        qty 0  price 70
        qty 200 price 60
        """
        super(TestAgreementOnChange, self).setUp()
        self.commonsetUp()
        start_date = self.now + timedelta(days=10)
        start_date = start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        end_date = self.now + timedelta(days=20)
        end_date = end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.agreement = self.agreement_model.create(
            {'supplier_id': self.supplier_id,
             'product_id': self.product_id,
             'start_date': start_date,
             'end_date': end_date,
             'delay': 5,
             'draft': False,
             'quantity': 1500})
        pl = self.agreement_pl_model.create(
            {'framework_agreement_id': self.agreement.id,
             'currency_id': self.ref('base.EUR')}
        )
        self.agreement_line_model.create(
            {'framework_agreement_pricelist_id': pl.id,
             'quantity': 0,
             'price': 70}
        )
        self.agreement_line_model.create(

            {'framework_agreement_pricelist_id': pl.id,
             'quantity': 200,
             'price': 60}
        )
        self.po_line_model = self.env['purchase.order.line']

    def test_00_price_change(self):
        """Ensure that on change price observer raise correct warning

        Warning must be risen if there is a running price agreement

        """

        with self.assertRaises(exceptions.Warning) as exc:
            self.po_line_model._onchange_price(
                20.0,
                self.agreement.id,
                currency=self.browse_ref('base.EUR'),
                qty=100
            )
        self.assertEqual(
            exc.exception.message,
            'You have set the price to 20.0'
            ' \n but there is a running agreement with price 70.0'
        )

    def test_01_price_change_bindings(self):
        """Check that change of price has correct behavior"""
        pl = self.agreement.supplier_id.property_product_pricelist_purchase.id
        with self.assertRaises(Exception) as exc:
            self.po_line_model.onchange_price(
                20.0,
                self.agreement.id,
                200,
                pl,
                self.agreement.product_id.product_variant_ids[0].id
            )
        self.assertEqual(
            exc.exception.message,
            'You have set the price to 20.0 \n '
            'but there is a running agreement with price 60.0'
        )

    def test_04_product_observer_bindings(self):
        """Check that change of product has correct behavior"""
        pl = self.agreement.supplier_id.property_product_pricelist_purchase.id
        LineContext = self.po_line_model.with_context(
            {'agreement_id': self.agreement.id}
        )
        LineContext.onchange_product_id(
            pl,
            self.agreement.product_id.product_variant_ids[0].id,
            200,
            self.agreement.product_id.uom_id.id,
            self.agreement.supplier_id.id,
            date_order=self.agreement.start_date + ' 00:00:00',
            fiscal_position_id=False,
            date_planned=False,
            name=False,
            price_unit=False,
            state='draft',
        )
