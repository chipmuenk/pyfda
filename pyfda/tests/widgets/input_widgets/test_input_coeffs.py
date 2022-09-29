# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:57:19 2017

@author: Christian Muenker
"""
import sys
import unittest
import logging

from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qset_cmb_box
from pyfda.libs.compat import (
    Qt, QTest, QSignalSpy, QPoint, QApplication, QTableWidgetItem)
from pyfda.input_widgets.input_coeffs import Input_Coeffs

app = QApplication(sys.argv)


class FilterCoeffsTest(unittest.TestCase):
    '''Test the FilterCoeffs GUI'''

    def init(self):
        '''Create the GUI'''
        self.form = Input_Coeffs()
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
        Set combobox `name` to item `arg`. Throw an error if the item
        doesn't exist in the combobox list.
        """
        if not cmb_wdg.isVisible():
            self.fail("Widget is not visible.")
        if not cmb_wdg.isEnabled():
            self.fail("Widget is not enabled.")
        else:
            # insure that cmbbox always fires an index changed signal
            # cmb_wdg.setCurrentIndex(-1)
            ret = qset_cmb_box(cmb_wdg, arg, fireSignals=True)
            # self.log.warning(f"return {ret}-{arg}")
            self.assertTrue(ret > -1, "String not contained in combo box")  # assert that arg exists in combo box

    def set_table_value(self, col, row, val):
        item = self.form.tblCoeff.item(row, col)
        if False:  #item:  # does item exist?
            item.setText(str(val))
        else:  # no, construct it:
            self.form.tblCoeff.setItem(row, col, QTableWidgetItem(str(val)))
            self.log.warning(f"Write table, return = {type(self.form.tblCoeff.item(row, col))})")
            self.log.warning(f"Row, col = {row, col})")
            self.log.warning(f"Row, col = {self.form.tblCoeff.rowCount(), self.form.tblCoeff.columnCount()})")
        #item_text = self.form.tblCoeff.item(1,1).text()
        #self.log.warning(f"Write table, return = {type(item_text)})")
        return

    def get_table_value(self, col, row):
        return str(self.form.tblCoeff.item(row, col))

    def set_lineedit_value(self, edit_wdg, arg):
        edit_wdg.clear()
        QTest.keyClicks(edit_wdg, arg)
        # name.setText(str(arg))
        # QtTest.QTest.keyPress(name.setText(), Qt.Key_Enter, NULL, 100)
        # QtTest.QTest.keyRelease(name.setText(), Qt.Key_Enter, NULL, 100)

    def initialize_form(self):
        """ utility function for initializing the form """
        self.ui.spnDigits.setValue(4)
        # self.ui.ledScale.setText("1.5")
        self.set_cmb_box(self.ui.cmbFilterType, 'FIR')
        spy = QSignalSpy(self.form.sig_tx)
        self.set_cmb_box(self.ui.cmb_fx_base, 'Float')
        # Push <Delete Table> Button with the left mouse button
        QTest.mouseClick(self.ui.butClear, Qt.LeftButton)

    def initialize_fixpoint_format(self):
        self.set_cmb_box(self.ui.cmb_fx_base, 'Dec')
        self.set_lineedit_value(self.ui.ledW, "8")
        # The following triggers recalculation of scale etc.
        self.set_cmb_box(self.ui.cmbQFrmt, 'Integer')
        self.set_cmb_box(self.ui.cmbQOvfl, 'sat')
        self.set_cmb_box(self.ui.cmbQuant, 'round')

        self.assertEqual(self.ui.ledScale.text(), "128")
        self.assertEqual(self.ui.ledWI.text(), "7")
        self.assertEqual(self.ui.ledWF.text(), "0")
# ==============================================================================
    def test_defaults(self):
        """Test GUI setting in its default state"""
        self.init()
        self.assertEqual(self.ui.spnDigits.value(), 4)
        self.assertEqual(qget_cmb_box(self.ui.cmbFilterType, data=False), "FIR")

        self.assertEqual(qget_cmb_box(self.ui.cmb_fx_base, data=False).lower(), "float")
        self.assertEqual(self.ui.butSetZero.text(), "= 0")

        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 1)
        self.assertEqual(self.form.tblCoeff.item(0, 0).text(), "1")
        self.log.warning("test_defaults finished")

# ------------------------------------------------------------------------------
    def test_cmb_filter_type(self):
        """Test setting <Filter Type> ComboBox and the effect on the table shape"""
        self.init()
        self.set_cmb_box(self.ui.cmbFilterType, 'IIR')
        self.assertEqual(qget_cmb_box(self.ui.cmbFilterType, data=False), "IIR")
        self.ui.cmbFilterType.currentIndexChanged.emit(1)
        QTest.mouseClick(self.ui.cmbFilterType, Qt.LeftButton)
        QTest.keyClick(QApplication.instance().focusWidget(), Qt.Key_PageDown)
        QTest.qWait(1000)
        QTest.keyClick(QApplication.instance().focusWidget(), Qt.Key_Return)
        QTest.qWait(1000)
        self.assertEqual(qget_cmb_box(self.ui.cmbFilterType, data=False), "IIR")
        # https://vicrucann.github.io/tutorials/qttest-signals-qtreewidget/
        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 2)
        item_10 = self.form.tblCoeff.item(0, 1)  # row, col
        self.assertEqual(float(item_10.text()), 1)

        self.set_cmb_box(self.ui.cmbFilterType, 'FIR')

        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 1)
        self.log.warning("test_cmb_filter_type finished")

# ==============================================================================
    def test_fixpoint_defaults(self):
        """Test fixpoint setting in its default state"""
        self.init()
        self.set_cmb_box(self.ui.cmb_fx_base, 'Dec')
        self.assertEqual(self.ui.spnDigits.value(), 4)
        self.assertEqual(qget_cmb_box(self.ui.cmbFilterType, data=False), "FIR")

        self.assertEqual(self.ui.ledW.text(), "16")
        self.assertEqual(self.ui.ledWF.text(), "15")
        self.assertEqual(self.ui.ledWI.text(), "0")
        self.assertEqual(qget_cmb_box(self.ui.cmb_fx_base, data=False).lower(), "dec")
        self.assertEqual(self.get_cmb_box(self.ui.cmbQOvfl), 'wrap')
        self.assertEqual(self.get_cmb_box(self.ui.cmbQuant), 'floor')
        self.assertEqual(self.ui.butSetZero.text(), "= 0")

        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 1)
        self.assertEqual(self.form.tblCoeff.item(0, 0).text(), "1")
        self.log.warning("test_fixpoint_defaults finished")

# ------------------------------------------------------------------------------
    def test_but_clear(self):
        """Test <Clear Table> Button"""
        self.init()
        self.set_cmb_box(self.ui.cmbFilterType, 'IIR')

        item_10 = self.form.tblCoeff.item(1, 0)  # row, col
        self.assertEqual(item_10.text(), "1")

        # Push <Delete Table> Button with the left mouse button
        QTest.mouseClick(self.ui.butClear, Qt.LeftButton)

        self.assertEqual(float(self.form.tblCoeff.item(1, 0).text()), 0)
        self.assertEqual(self.form.tblCoeff.rowCount(), 2)
        self.assertEqual(self.form.tblCoeff.columnCount(), 2)
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
        self.initialize_fixpoint_format()
        self.assertEqual(self.form.tblCoeff.isVisible(), True)
        self.assertEqual(self.form.tblCoeff.isEnabled(), True)
        x = self.form.tblCoeff.columnViewportPosition(0)
        y = self.form.tblCoeff.rowViewportPosition(1)
        QTest.mouseClick(self.form.tblCoeff.viewport(), Qt.LeftButton,
                         Qt.NoModifier, QPoint(x, y))
        QTest.keyClicks(QApplication.instance().focusWidget(), "13", delay=100)
        # QTest.keyClick(QApplication.instance().focusWidget(), Qt.Key_Return, delay=1000)
        QTest.mouseClick(self.ui.butSave, Qt.LeftButton)
        QTest.qWait(1000)
        # self.set_table_value(1, 0, 25)  # row, col, value
        self.assertEqual(self.form.tblCoeff.item(0, 0).text(), "1.0")
        self.assertEqual(self.form.tblCoeff.item(1, 0).text(), "0.0078125")
        # self.assertEqual(self.get_table_value(1, 0), "1")

        # self.assertEqual(self.get_table_value(1, 1), "15")

        # self.assertEqual(self.form.tblCoeff.rowCount(), 2)
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
    """run tests with python -m pyfda.tests.widgets.test_input_coeffs"""
    unittest.main()
