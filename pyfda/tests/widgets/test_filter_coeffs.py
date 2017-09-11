# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:57:19 2017

@author: Christian Muenker
"""


import sys
import unittest
from pyfda.pyfda_qt_lib import qget_cmb_box, qset_cmb_box

from ...compat import Qt, QtTest, QApplication

from pyfda.input_widgets.filter_coeffs import FilterCoeffs

app = QApplication(sys.argv)

class FilterCoeffsTest(unittest.TestCase):
    '''Test the FilterCoeffs GUI'''
    
    def setUp(self):
        '''Create the GUI'''
        self.form = FilterCoeffs(None)

    def setFormValues(self):
        """ Set values for some fields """
        self.form.spnRound.setValue(7)
        self.form.ledScale.setText("1.0")

    def test_defaults(self):
        """Test GUI setting in its default state"""
        self.assertEqual(self.form.spnRound.value(), 4)
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
        
        qset_cmb_box(self.form.cmbFilterType, 'FIR', fireSignals=True)

        self.assertEqual(self.form.tblCoeff.rowCount(), 3)
        self.assertEqual(self.form.tblCoeff.columnCount(), 1)

    def test_but_clear(self):
        """Test <Delete Table> Button"""
        qset_cmb_box(self.form.cmbFilterType, 'IIR', fireSignals=True)
        
        item_10 = self.form.tblCoeff.item(1,0) # row, col
        self.assertEqual(item_10.text(), "1")

        # Push <Delete Table> Button with the left mouse button 
        QtTest.QTest.mouseClick(self.form.butClear, Qt.LeftButton)
        # self.assertEqual(self.form.jiggers, 36.0)
        self.assertEqual(self.form.tblCoeff.item(1,0).text(), "0")
        self.assertEqual(self.form.tblCoeff.rowCount(), 2)
        self.assertEqual(self.form.tblCoeff.columnCount(), 2)

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

# run tests with python -m pyfda.tests.widgets.test_filter_coeffs
