# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:57:19 2017

@author: Christian Muenker
"""
import sys
import unittest
import logging

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qset_cmb_box
from pyfda.libs.compat import Qt, QApplication
from PyQt5.QtTest import QTest
from pyfda.input_widgets.input_coeffs import InputCoeffs

app = QApplication(sys.argv)


class FilterCoeffsTest(unittest.TestCase):
    '''Test the FilterCoeffs GUI'''

    def setUp(self):
        fb.fil_copy(src='ref', dest='0')

    def tearDown(self):
        if hasattr(self, 'form'):
            self.form.close()
        fb.fil_copy(src='ref', dest='0')

    def init(self):
        '''Create the GUI'''
        self.form = InputCoeffs()
        self.form.show()
        self.ui = self.form.ui
        self.log = logging.getLogger("LOG")

    def get_cmb_box(self, cmb_wdg):
        """
        get current text entry of combobox `cmb_wdg` (lower cased)
        """
        return qget_cmb_box(cmb_wdg, data=False).lower()

    def set_cmb_box(self, cmb_wdg, arg):
        """
        Set combobox `cmb_wdg` to item `arg`. Throw an error if the item
        doesn't exist in the combobox list.
        """
        if not cmb_wdg.isVisible():
            self.fail("Widget is not visible.")
        if not cmb_wdg.isEnabled():
            self.fail("Widget is not enabled.")
        else:
            # insure that cmbbox always fires an index changed signal
            # cmb_wdg.setCurrentIndex(-1)
            ret = qset_cmb_box(cmb_wdg, arg, fire_signals=True)
            # self.log.warning(f"return {ret}-{arg}")
            self.assertTrue(ret > -1, "String not contained in combo box")  # assert that arg exists in combo box

    def initialize_form(self):
        """ utility function for initializing the form """
        self.ui.spn_digits.setValue(4)
        self.set_cmb_box(self.ui.cmb_filter_type, 'FIR')
        self.set_cmb_box(self.ui.cmb_qfrmt, 'Float64')
        # Push <Delete Table> Button with the left mouse button
        QTest.mouseClick(self.ui.but_clear, Qt.LeftButton)
# ==============================================================================
    def test_defaults(self):
        """Test GUI setting in its default state"""
        self.init()
        self.assertEqual(self.ui.spn_digits.value(), 4)
        self.assertEqual(qget_cmb_box(self.ui.cmb_filter_type, data=False), "IIR")

        self.assertEqual(qget_cmb_box(self.ui.cmb_qfrmt, data=False), 'Float64')
        self.assertEqual(self.ui.but_set_zero.text(), "= 0")

        self.assertEqual(self.form.tbl_coeff.rowCount(), 5)
        self.assertEqual(self.form.tbl_coeff.columnCount(), 2)
        self.assertAlmostEqual(float(self.form.tbl_coeff.item(0, 0).text()), 0.005009993265049969)
        self.assertEqual(self.form.tbl_coeff.item(0, 1).text(), "1.0")
        self.log.warning("test_defaults finished")

# ------------------------------------------------------------------------------
    def test_cmb_filter_type(self):
        """Test setting <Filter Type> ComboBox and the effect on the table shape"""
        self.init()
        self.set_cmb_box(self.ui.cmb_filter_type, 'IIR')
        self.assertEqual(qget_cmb_box(self.ui.cmb_filter_type, data=False), "IIR")
        self.ui.cmb_filter_type.currentIndexChanged.emit(1)
        QTest.mouseClick(self.ui.cmb_filter_type, Qt.LeftButton)
        QTest.keyClick(QApplication.instance().focusWidget(), Qt.Key_PageDown)
        QTest.qWait(1000)
        QTest.keyClick(QApplication.instance().focusWidget(), Qt.Key_Return)
        QTest.qWait(1000)
        self.assertEqual(qget_cmb_box(self.ui.cmb_filter_type, data=False), "IIR")
        # https://vicrucann.github.io/tutorials/qttest-signals-qtreewidget/
        self.assertEqual(self.form.tbl_coeff.rowCount(), 5)
        self.assertEqual(self.form.tbl_coeff.columnCount(), 2)
        item_10 = self.form.tbl_coeff.item(0, 1)  # row, col
        self.assertEqual(float(item_10.text()), 1)

        self.set_cmb_box(self.ui.cmb_filter_type, 'FIR')

        self.assertEqual(self.form.tbl_coeff.rowCount(), 5)
        self.assertEqual(self.form.tbl_coeff.columnCount(), 2)
        self.assertEqual(fb.fb_get('ft'), 'fir')
        self.log.warning("test_cmb_filter_type finished")

# ==============================================================================
    def test_fixpoint_defaults(self):
        """Test fixpoint setting in its default state"""
        self.init()
        self.set_cmb_box(self.ui.cmb_qfrmt, 'Fractional')
        self.set_cmb_box(self.ui.cmb_fx_base, 'Dec')
        self.assertEqual(self.ui.spn_digits.value(), 4)
        self.assertEqual(qget_cmb_box(self.ui.cmb_filter_type, data=False), "IIR")

        self.assertEqual(self.ui.wdg_wq_coeffs_b.led_wf.text(), "15")
        self.assertEqual(self.ui.wdg_wq_coeffs_b.led_wi.text(), "0")
        self.assertEqual(qget_cmb_box(self.ui.cmb_fx_base, data=False).lower(), "dec")
        self.assertEqual(self.get_cmb_box(self.ui.wdg_wq_coeffs_b.cmb_ovfl), 'wrap')
        self.assertEqual(self.get_cmb_box(self.ui.wdg_wq_coeffs_b.cmb_quant), 'floor')
        self.assertEqual(self.ui.but_set_zero.text(), "= 0")

        self.assertEqual(self.form.tbl_coeff.rowCount(), 5)
        self.assertEqual(self.form.tbl_coeff.columnCount(), 2)
        self.assertAlmostEqual(float(self.form.tbl_coeff.item(0, 0).text()), 0.0050048828125)
        self.log.warning("test_fixpoint_defaults finished")

# ------------------------------------------------------------------------------
    def test_but_clear(self):
        """Test <Clear Table> Button"""
        self.init()
        self.set_cmb_box(self.ui.cmb_filter_type, 'IIR')

        item_10 = self.form.tbl_coeff.item(1, 0)  # row, col
        self.assertAlmostEqual(float(item_10.text()), 0.002969044992011087)

        # Push <Delete Table> Button with the left mouse button
        QTest.mouseClick(self.ui.but_clear, Qt.LeftButton)

        self.assertEqual(float(self.form.tbl_coeff.item(1, 0).text()), 0)
        self.assertEqual(self.form.tbl_coeff.rowCount(), 2)
        self.assertEqual(self.form.tbl_coeff.columnCount(), 2)
        self.log.warning("test_but_clear finished")

# ------------------------------------------------------------------------------
    def test_write_table(self):
        """
        Test writing to table in various formats
            https://www.francescmm.com/testing-qtablewidget-with-qtest/
            https://vicrucann.github.io/tutorials/qttest-signals-qtreewidget/
        """
        self.init()
        self.initialize_form()
        self.assertEqual(self.form.tbl_coeff.isVisible(), True)
        self.assertEqual(self.form.tbl_coeff.isEnabled(), True)
        self.form.tbl_coeff.setCurrentCell(1, 0)
        QTest.keyClick(self.form.tbl_coeff, Qt.Key_F2)
        QTest.qWait(50)
        editor = QApplication.instance().focusWidget()
        QTest.keyClick(editor, Qt.Key_A, Qt.ControlModifier)
        QTest.keyClicks(editor, "0.125", delay=100)
        QTest.keyClick(editor, Qt.Key_Return)
        QTest.qWait(50)
        QTest.mouseClick(self.ui.but_apply, Qt.LeftButton)
        self.assertAlmostEqual(float(fb.fb_get('ba')[0][1]), 0.125)
        self.assertEqual(self.form.tbl_coeff.item(1, 0).text(), "0.125")
        self.log.warning("test_write_table finished")

#    def test_shuffle(self):
#        # make sure the shuffled sequence does not lose any elements
#        random.shuffle(self.seq)
#        self.seq.sort()
#        self.assertEqual(self.seq, range(10))
#
#    def test_choice(self):
#        element = random.choice(self.seq)
#        self.assertTrue(element in self.seq)
#
#    def test_sample(self):
#        self.assertRaises(ValueError, random.sample, self.seq, 20)
#        for element in random.sample(self.seq, 5):
#            self.assertTrue(element in self.seq)

#
# ==============================================================================


if __name__ == '__main__':
    """run tests with python -m pyfda.tests.widgets.input_widgets.test_input_coeffs"""
    unittest.main()
