# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:57:19 2017

@author: Christian Muenker
"""


import sys
import unittest
import pytest
from pyfda.pyfda_qt_lib import qget_cmb_box, qset_cmb_box

from ...compat import Qt, QtTest, QApplication, QTableWidgetItem

from pyfda.input_widgets.input_coeffs import Input_Coeffs

app = QApplication(sys.argv)

class FilterCoeffsTest(unittest.TestCase):
    '''Test the FilterCoeffs GUI'''

    def setUp(self):
        '''Create the GUI'''
        self.form = Input_Coeffs(None)

    def set_cmb_box(self, cmb_wdg, arg):
        """
        Set combobox `name` to item `arg`. Throw an error if the item
        doesn't exist in the combobox list.
        """
        if not cmb_wdg.isVisible():
            self.fail("Widget is not visible.")
        elif not cmb_wdg.isEnabled():
            self.fail("Widget is not enabled.")
        else:
            cmb_wdg.setCurrentIndex(-1) # insure that cmbbox always fires an index changed signal
            ret = qset_cmb_box(cmb_wdg, arg, fireSignals=True)
            self.assertIsNot(ret, -1) # assert that arg exists in combo box

    def set_table_value(self, col, row, val):
        item = self.form.tblCoeff.item(row, col)
        if item: # does item exist?
            item.setText(str(val))
        else: # no, construct it:
            self.form.tblCoeff.setItem(row, col, QTableWidgetItem(str(val)))
        return self.form.tblCoeff.item(row, col).text()

    def get_table_value(self, col, row):
        item = self.form.tblCoeff.item(row, col)
        return str(item.text())

    def set_lineedit_value(self, edit_wdg, arg):
        edit_wdg.clear()
        QtTest.QTest.keyClicks(edit_wdg, arg)
        # name.setText(str(arg))
        # QtTest.QTest.keyPress(name.setText(), Qt.Key_Enter, NULL, 100)
        # QtTest.QTest.keyRelease(name.setText(), Qt.Key_Enter, NULL, 100)


    def initialize_form(self):
        """ utility function for initializing the form """
        self.form.spnDigits.setValue(4)
        self.form.ledScale.setText("1.5")
        self.set_cmb_box(self.form.cmbFilterType, 'FIR')
        self.set_cmb_box(self.form.cmbFormat, 'Float')

        # Push <Delete Table> Button with the left mouse button
        QtTest.QTest.mouseClick(self.form.butClear, Qt.LeftButton)

    def initialize_fixpoint_format(self):

        self.set_cmb_box(self.form.cmbFormat, 'Dec')
#        self.form.ledW.setText("4")
        self.set_lineedit_value(self.form.ledW, "4")
        # The following triggers recalculation of scale etc.
        self.set_cmb_box(self.form.cmbQFrmt, 'Integer')
        self.set_cmb_box(self.form.cmbQOvfl, 'sat')
        self.set_cmb_box(self.form.cmbQuant, 'round')

        self.assertEqual(self.form.ledScale.text(), "8")

    def test_defaults(self):
        """Test GUI setting in its default state"""
        self.assertEqual(self.form.spnDigits.value(), 4)
        self.assertEqual(self.form.ledW.text(), "16")
        self.assertEqual(self.form.ledWF.text(), "0")
        self.assertEqual(self.form.ledWI.text(), "15")
        self.assertEqual(qget_cmb_box(self.form.cmbFormat, data=False).lower(), "float")
        self.assertEqual(self.form.butSetZero.text(), "= 0")

        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 1)
        self.assertEqual(self.form.tblCoeff.item(0,0).text(), "1")

    def test_cmb_filter_type(self):
        """Test <Filter Type> ComboBox"""
        self.assertEqual(qget_cmb_box(self.form.cmbFilterType, data=False), "IIR")
        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 2)

        self.set_cmb_box(self.form.cmbFilterType, 'FIR')

        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 1)

    def test_but_clear(self):
        """Test <Clear Table> Button"""
        qset_cmb_box(self.form.cmbFilterType, 'IIR', fireSignals=True)

        item_10 = self.form.tblCoeff.item(1,0) # row, col
        self.assertEqual(item_10.text(), "1")

        # Push <Delete Table> Button with the left mouse button
        QtTest.QTest.mouseClick(self.form.butClear, Qt.LeftButton)
        # self.assertEqual(self.form.jiggers, 36.0)
        self.assertEqual(self.form.tblCoeff.item(1,0).text(), "0")
        self.assertEqual(self.form.tblCoeff.rowCount(), 2)
        self.assertEqual(self.form.tblCoeff.columnCount(), 2)

    def test_write_table(self):
        """Test writing to table in various formats"""
        self.initialize_form()
        #self.initialize_fixpoint_format()

        ret = self.set_table_value(1,1, 25) # row, col, value
        print("set\n", ret)
        self.assertEqual(self.get_table_value(1,1), "25")

        self.set_cmb_box(self.form.cmbFormat, 'Dec')
        self.set_cmb_box(self.form.cmbQFrmt, 'Integer')
        self.assertEqual(self.form.ledScale.text(), "8")
        self.set_cmb_box(self.form.cmbFormat, 'Float')

        self.assertEqual(self.get_table_value(1,1), "15")

        self.assertEqual(self.form.tblCoeff.rowCount(), 2)


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
#==============================================================================


if __name__=='__main__':
    unittest.main()

# run tests with python -m pyfda.tests.widgets.test_input_coeffs
