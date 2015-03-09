# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter Poles and Zeros
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
#import scipy.io
import numpy as np
from scipy.signal import tf2zpk, zpk2tf

# https://github.com/danthedeckie/simpleeval

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb # importing filterbroker initializes all its globals
from simpleeval import simple_eval

# TODO: drag & drop doesn't work
# TODO: insert row above currently selected row instead of appending at the end
# TODO: Add quantizer widget
# TODO: eliminate trailing zeros for filter order calculation
# TODO: IIR button functionality not yet implemented
def cround(x, n_dig = 0):
    """
    round complex number to n_dig digits. If n_dig == 0, don't round at all,
    just convert complex numbers with an imaginary part very close to zero to
    real.
    """
    x = np.real_if_close(x, 1e-15)
    if n_dig > 0:
        if np.iscomplex(x):
            x = round(x.real, n_dig) + 1j * round(x.imag, n_dig)
        else:
            x = round(x, n_dig)
    return x

class InputPZ(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputPZ, self).__init__()

        self.initUI()

    def initUI(self):
        """
        Intitialize the widget, consisting of:
        -
        -
        """
        # widget / subwindow for Pole/Zero display / entry

        self.chkPZList =  QtGui.QCheckBox()
        self.chkPZList.setChecked(True)
        self.chkPZList.setToolTip("Show filter Poles / Zeros as an editable list.")
        self.lblPZList = QtGui.QLabel()
        self.lblPZList.setText("Show Poles / Zeros")

        self.lblRound = QtGui.QLabel("Digits = ")
        self.spnRound = QtGui.QSpinBox()
        self.spnRound.setRange(0,9)
        self.spnRound.setValue(0)
        self.spnRound.setToolTip("Round to d digits.")

        self.lblGain = QtGui.QLabel()
        self.lblGain.setText("k = ")

        self.ledGain = QtGui.QLineEdit()
        self.ledGain.setToolTip("Specify gain factor k.")
        self.ledGain.setText(str(1.))

        self.tblPZ = QtGui.QTableWidget()
        self.tblPZ.setEditTriggers(QtGui.QTableWidget.AllEditTriggers)
        self.tblPZ.setAlternatingRowColors(True)
        self.tblPZ.setDragEnabled(True)
        self.tblPZ.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.tblPZ.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                          QtGui.QSizePolicy.MinimumExpanding)

        self.butAddRow = QtGui.QPushButton()
        self.butAddRow.setToolTip("Add row to PZ table.\n"
                                "Select n existing rows to append n new rows.")
        self.butAddRow.setText("Add")

        self.butDelRow = QtGui.QPushButton()
        self.butDelRow.setToolTip("Delete selected row(s) from the table.\n"
                "Multiple rows can be selected using <SHIFT> or <CTRL>."
                "If nothing is selected, delete last row.")
        self.butDelRow.setText("Delete")

        self.butClear = QtGui.QPushButton()
        self.butClear.setToolTip("Clear all entries.")
        self.butClear.setText("Clear")

        self.butSave = QtGui.QPushButton()
        self.butSave.setToolTip("Save P/Z & update all plots.\n"
                                "No modifications are saved before!")
        self.butSave.setText("Save")

        self.butLoad = QtGui.QPushButton()
        self.butLoad.setToolTip("Reload P / Z.")
        self.butLoad.setText("Load")

        self.butSetZero = QtGui.QPushButton()
        self.butSetZero.setToolTip("Set P / Z = 0 with a magnitude < eps.")
        self.butSetZero.setText("Set Zero")

        self.lblEps = QtGui.QLabel()
        self.lblEps.setText("for b, a <")

        self.ledSetEps = QtGui.QLineEdit()
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        # ============== UI Layout =====================================
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkPZList)
        self.layHChkBoxes.addWidget(self.lblPZList)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblRound)
        self.layHChkBoxes.addWidget(self.spnRound)
#        self.layHChkBoxes.addStretch(10)

        self.layHGain = QtGui.QHBoxLayout()
        self.layHGain.addWidget(self.lblGain)
        self.layHGain.addWidget(self.ledGain)
        self.layHGain.addStretch(10)

        self.layHButtonsPZs1 = QtGui.QHBoxLayout()
        self.layHButtonsPZs1.addWidget(self.butAddRow)
        self.layHButtonsPZs1.addWidget(self.butDelRow)
        self.layHButtonsPZs1.addWidget(self.butSave)
        self.layHButtonsPZs1.addWidget(self.butLoad)
        self.layHButtonsPZs1.addStretch()

        self.layHButtonsPZs2 = QtGui.QHBoxLayout()
        self.layHButtonsPZs2.addWidget(self.butClear)
        self.layHButtonsPZs2.addWidget(self.butSetZero)
        self.layHButtonsPZs2.addWidget(self.lblEps)
        self.layHButtonsPZs2.addWidget(self.ledSetEps)
        self.layHButtonsPZs2.addStretch()

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addLayout(self.layHGain)
        layVMain.addLayout(self.layHButtonsPZs1)
        layVMain.addLayout(self.layHButtonsPZs2)
        layVMain.addWidget(self.tblPZ)
        layVMain.addStretch(1)
        self.setLayout(layVMain)
        self.showZPK() # initialize table with default values from filterbroker

        # ============== Signals & Slots ================================
#        self.tblPZ.itemEntered.connect(self.savePZs) # nothing happens
#        self.tblPZ.itemActivated.connect(self.savePZs) # nothing happens
        self.spnRound.editingFinished.connect(self.showZPK)
        self.butLoad.clicked.connect(self.showZPK)
        self.chkPZList.clicked.connect(self.showZPK)

#        self.ledGain.editingFinished.connect(self.saveZPK)
#        self.tblPZ.itemChanged.connect(self.saveZPK) # works but fires multiple times
#        self.tblPZ.selectionModel().currentChanged.connect(self.saveZPK)
#        self.tblPZ.clicked.connect(self.saveZPK)
        self.butSave.clicked.connect(self.saveZPK)

        self.butDelRow.clicked.connect(self.deleteRows)
        self.butAddRow.clicked.connect(self.addRows)
        self.butClear.clicked.connect(self.clearTable)

        self.butSetZero.clicked.connect(self.setZPKZero)

    def clearTable(self):
        """
        Clear table & initialize zpk for two poles and zeros @ origin,
        P = Z = [0; 0], k = 1
        """
        self.tblPZ.clear()
        self.tblPZ.setRowCount(2)

        self.ledGain.setText("1.0")

        num_cols = self.tblPZ.columnCount()
        for row in range(2):
            for col in range(num_cols):
                self.tblPZ.setItem(row,col,QtGui.QTableWidgetItem("0.0"))

    def saveZPK(self):
        """
        Read out table and save the values to the filter PZ dict
        """
        if self.DEBUG:
            print("=====================\nInputPZ.saveZPK")
        zpk = []
        num_rows = self.tblPZ.rowCount()
        if self.DEBUG: print("nrows:",num_rows)

        for col in range(2):
            rows = []
            for row in range(num_rows):
                item = self.tblPZ.item(row, col)
                if item:
                    if item.text() != "":
                        rows.append(simple_eval(item.text()))
                else:
                    rows.append(0.)

            zpk.append(rows)

        zpk.append(simple_eval(self.ledGain.text()))
#        print("ZPK - Gain:",zpk[2])

        fb.fil[0]['zpk'] = zpk

#        bb = zpk[2] * np.poly(zpk[0])
#        aa = zpk[2] * np.poly(zpk[1])
#        fb.fil[0]['coeffs'] = (bb,aa)
        fb.fil[0]['coeffs'] = zpk2tf(zpk[0], zpk[1], zpk[2])

        fb.fil[0]["N"] = num_rows-1
        fb.fil[0]['creator'] = ('zpk', 'input_pz')

        if self.DEBUG:
            print("ZPK - coeffs:",  fb.fil[0]['coeffs'])
            print("ZPK - zpk:",  fb.fil[0]['zpk'])
            print("ZPK updated!")

    def showZPK(self):
        """
        Create table from filter zpk dict, overwriting all previous entries.
        """
        zpk = fb.fil[0]['zpk']
        n_digits = int(self.spnRound.text())
        self.ledGain.setVisible(self.chkPZList.isChecked())
        self.lblGain.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setVisible(self.chkPZList.isChecked())

#        self.ledGain.setText(str(zpk[2]))# update gain k
        self.ledGain.setText(str(cround(zpk[2], n_digits)))

        self.tblPZ.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setRowCount(max(len(zpk[0]),len(zpk[1])))

        if self.DEBUG:
            print("=====================\nInputZPK.showZPK")
            print("ZPK:\n",zpk)
            print ("shape", np.shape(zpk))
            print ("len", len(zpk))
            print("ndim", np.ndim(zpk))

        self.tblPZ.setColumnCount(2)
        self.tblPZ.setHorizontalHeaderLabels(["Z", "P"])
        for col in range(2):
            for row in range(len(zpk[col])):
                if self.DEBUG:print("Len Row:", len(zpk[col]))
                item = self.tblPZ.item(row, col)
                if item:
                    item.setText(str(cround(zpk[col][row], n_digits)))
                else:
                    self.tblPZ.setItem(row,col,QtGui.QTableWidgetItem(
                                    str(cround(zpk[col][row], n_digits))))

        self.tblPZ.resizeColumnsToContents()
        self.tblPZ.resizeRowsToContents()

    def deleteRows(self):
        """
        Delete all selected rows by:
        - reading the indices of all selected cells
        - collecting the row numbers in a set (only unique elements)
        - sort the elements in a list in descending order
        - delete the rows starting at the bottom
        If nothing is selected, delete last row.
        """
        old_rows = self.tblPZ.rowCount()
        indices = self.tblPZ.selectionModel().selectedIndexes()
        rows = set()
        for index in indices:
            rows.add(index.row()) # collect all selected rows in a set
        if len(rows) == 0:
            rows = {old_rows-1}
        rows = sorted(list(rows), reverse = True)# sort rows in decending order
        for r in rows:
            self.tblPZ.removeRow(r)

        self.tblPZ.setRowCount(old_rows - len(rows))

    def addRows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add 1 row.
        """
        old_rows = self.tblPZ.rowCount()
        new_rows = len(self.tblPZ.selectionModel().selectedRows()) + old_rows
        self.tblPZ.setRowCount(new_rows)

        if old_rows == new_rows: # nothing selected
            new_rows = old_rows + 1 # add at least one row

        self.tblPZ.setRowCount(new_rows)

        for col in range(2):
            for row in range(old_rows, new_rows):
                self.tblPZ.setItem(row,col,QtGui.QTableWidgetItem("0.0"))

        self.tblPZ.resizeColumnsToContents()
        self.tblPZ.resizeRowsToContents()

    def setZPKZero(self):
        """
        Set all PZs = 0 with a magnitude less than eps
        """
        eps = float(self.ledSetEps.text())
        num_rows= self.tblPZ.rowCount()

        for col in range(2):
            for row in range(num_rows):
                item = self.tblPZ.item(row, col)
                if item:
                    if abs(simple_eval(item.text())) < eps:
                        item.setText(str(0.))
                else:
                    self.tblPZ.setItem(row,col,QtGui.QTableWidgetItem("0.0"))

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputPZ()
    form.show()

    app.exec_()