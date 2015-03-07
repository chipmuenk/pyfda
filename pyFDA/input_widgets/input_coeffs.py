# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter coefficients
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal
#import scipy.io
import numpy as np
from scipy.signal import tf2zpk

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
# TODO: emit signal when table is changed : careful, saveCoeffs must not be
#        triggered when table is changed by program!!!

class InputCoeffs(QtGui.QWidget):
    """
    Create widget for viewing / editing / entering data
    """
        # class variables (shared between instances if more than one exists)
    coeffsChanged = pyqtSignal()  # emitted when coeffs have been changed
                                    # manually
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputCoeffs, self).__init__()

        self.initUI()

    def initUI(self):
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """

        self.chkCoeffList =  QtGui.QCheckBox()
        self.chkCoeffList.setChecked(True)
        self.chkCoeffList.setToolTip("Show filter coefficients as an editable list.")
        self.lblCoeffList = QtGui.QLabel()
        self.lblCoeffList.setText("Show Coefficients")

        self.chkIIR =  QtGui.QCheckBox()
        self.chkIIR.setChecked(True)
        self.chkIIR.setToolTip("IIR Filter")
#        self.chkIIR.setCheckable(False) # not implemented yet
#        self.chkIIR.setEnabled(False) # not implemented yet
        self.lblIIR = QtGui.QLabel()
        self.lblIIR.setText("IIR")

        self.tblCoeff = QtGui.QTableWidget()
        self.tblCoeff.setEditTriggers(QtGui.QTableWidget.AllEditTriggers)
        self.tblCoeff.setAlternatingRowColors(True)
        self.tblCoeff.setDragEnabled(True)
        self.tblCoeff.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.tblCoeff.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                          QtGui.QSizePolicy.MinimumExpanding)

        self.butAddRow = QtGui.QPushButton()
        self.butAddRow.setToolTip("Add row to coefficient table.\nSelect n existing rows to append n new rows.")
        self.butAddRow.setText("Add")

        self.butDelRow = QtGui.QPushButton()
        self.butDelRow.setToolTip("Delete selected row(s) from the table.\n"
                "Multiple rows can be selected using <SHIFT> or <CTRL>.")
        self.butDelRow.setText("Delete")

        self.butClear = QtGui.QPushButton()
        self.butClear.setToolTip("Clear all entries.")
        self.butClear.setText("Clear")

        self.butSave = QtGui.QPushButton()
        self.butSave.setToolTip("Save coefficients & update filter plots.")
        self.butSave.setText("Save")

        self.butSetZero = QtGui.QPushButton()
        self.butSetZero.setToolTip("Set coefficients = 0 with a magnitude < eps.")
        self.butSetZero.setText("Set Zero")

        self.lblEps = QtGui.QLabel()
        self.lblEps.setText("for b, a <")

        self.ledSetEps = QtGui.QLineEdit()
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        # ============== UI Layout =====================================
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkCoeffList)
        self.layHChkBoxes.addWidget(self.lblCoeffList)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.chkIIR)
        self.layHChkBoxes.addWidget(self.lblIIR)
#        self.layHChkBoxes.addStretch(10)

        self.layHButtonsCoeffs1 = QtGui.QHBoxLayout()
        self.layHButtonsCoeffs1.addWidget(self.butAddRow)
        self.layHButtonsCoeffs1.addWidget(self.butDelRow)
        self.layHButtonsCoeffs1.addWidget(self.butClear)
        self.layHButtonsCoeffs1.addWidget(self.butSave)
        self.layHButtonsCoeffs1.addStretch()

        self.layHButtonsCoeffs2 = QtGui.QHBoxLayout()
        self.layHButtonsCoeffs2.addWidget(self.butSetZero)
        self.layHButtonsCoeffs2.addWidget(self.lblEps)
        self.layHButtonsCoeffs2.addWidget(self.ledSetEps)
        self.layHButtonsCoeffs2.addStretch()

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addWidget(self.tblCoeff)
        layVMain.addLayout(self.layHButtonsCoeffs1)
        layVMain.addLayout(self.layHButtonsCoeffs2)
#        layVMain.addStretch(1)
        self.setLayout(layVMain)
        self.showCoeffs() # initialize table with default values from fb

        # ============== Signals & Slots ================================
#        self.tblCoeff.itemEntered.connect(self.saveCoeffs) # nothing happens
#        self.tblCoeff.itemActivated.connect(self.saveCoeffs) # nothing happens
        # this works but fires multiple times _and_ fires every time cell is 
        # changed by program as well!
#        self.tblCoeff.itemChanged.connect(self.saveCoeffs) 
#        self.tblCoeff.clicked.connect(self.saveCoeffs)
#        self.tblCoeff.selectionModel().currentChanged.connect(self.saveCoeffs)
        self.butSave.clicked.connect(self.saveCoeffs)

        self.chkCoeffList.clicked.connect(self.showCoeffs)

        self.butDelRow.clicked.connect(self.deleteRows)
        self.butAddRow.clicked.connect(self.addRows)
        self.butClear.clicked.connect(self.clearTable)

        self.butSetZero.clicked.connect(self.setCoeffsZero)

    def saveCoeffs(self):
        """
        Read out coefficients table and save the values to filter 'coeffs' 
        and 'zpk' dicts. Is called by <Update> and every time a cell is clicked
        """
        if self.DEBUG:
            print("=====================\nInputCoeffs.saveCoeffs")
        coeffs = []
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        if self.DEBUG: print("Tbl rows /  cols:", num_rows, num_cols)
        if num_cols > 1: # IIR
            for col in range(num_cols):
                rows = []
                for row in range(num_rows):
                    item = self.tblCoeff.item(row, col)
                    if item:
                        if item.text() != "":
                            rows.append(simple_eval(item.text()))
                    else:
                        rows.append(0.)
#                    rows.append(float(item.text()) if item else 0.)
                coeffs.append(rows)
        else: # FIR
            self.chkIIR.setChecked(False)
            col = 0
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if item:
                    if item.text() != "":
                        coeffs.append(simple_eval(item.text()))
                else:
                    coeffs.append(0.)

        fb.fil[0]['coeffs'] = coeffs # np.array(coeffs, dtype = 'float64')
        
        if np.ndim(coeffs) == 1:
            fb.fil[0]["zpk"] = tf2zpk(coeffs[0], [1], np.zeros(len(coeffs[0]-1)))
            if self.DEBUG: print("Coeffs - FIR:",  coeffs)
        else:
            fb.fil[0]["zpk"] = tf2zpk(coeffs[0],coeffs[1]) # convert to poles / zeros
            if self.DEBUG: print("Coeffs - IIR:", coeffs)
        fb.fil[0]["N"] = num_rows-1
        fb.fil[0]['creator'] = ('ba', 'input_coeffs')

        if self.DEBUG:
            print("Coeffs - ZPK:", fb.fil[0]["zpk"])
            print ("Coeffs updated!")

    def showCoeffs(self):
        """
        Create table from filter coeff dict
        """
        coeffs = fb.fil[0]["coeffs"]
        self.tblCoeff.setVisible(self.chkCoeffList.isChecked())

        self.tblCoeff.setRowCount(max(np.shape(coeffs)))

        if self.DEBUG:
            print("=====================\nInputCoeffs.showCoeffs")
            print("Coeffs:\n",coeffs)
            print ("shape", np.shape(coeffs))
            print ("len", len(coeffs))
            print("ndim", np.ndim(coeffs))

        if np.ndim(coeffs) == 1: # FIR
            self.chkIIR.setChecked(False) 
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])
            for row in range(len(coeffs)):
                if self.DEBUG: print(row, coeffs[row])
                item = self.tblCoeff.item(row, 0)
                if item:
                    item.setText(str(coeffs[row]))
                else:
                    self.tblCoeff.setItem(row,0,QtGui.QTableWidgetItem(
                                    str(coeffs[row])))
        else: # IIR
            self.chkIIR.setChecked(True) 
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
            for col in range(2):
                for row in range(np.shape(coeffs)[1]):
                    item = self.tblCoeff.item(row, col)
                    if item:
                        item.setText(str(coeffs[col][row]))
                    else:
                        self.tblCoeff.setItem(row,col,QtGui.QTableWidgetItem(
                                                        str(coeffs[col][row])))
        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()

    def deleteRows(self):
        """
        Delete all selected rows by: 
        - reading the indices of all selected cells
        - collecting the row numbers in a set (only unique elements)
        - sort the elements in a list in descending order
        - delete the rows starting at the bottom
        """
        # returns index to rows: 
#        rows = self.tblCoeff.selectionModel().selectedRows()
        indices = self.tblCoeff.selectionModel().selectedIndexes()
        rows = set() 
        for index in indices:
            rows.add(index.row()) # collect all selected rows in a set
        rows = sorted(list(rows), reverse = True)# sort rows in decending order
        for r in rows:
#            self.tblCoeff.removeRow(r.row())
            self.tblCoeff.removeRow(r)
#        self.updateCoeffs()

    def addRows(self):
        """
        Add the number of selected rows to the table.
        If nothing is selected, add 1 row. Afterwards, refresh
        the table and save. 
        """
        nrows = len(self.tblCoeff.selectionModel().selectedRows())

        if nrows == 0:
            nrows = 1 # add at least one row
        ncols = self.tblCoeff.columnCount()

        if ncols == 1: # FIR
            fb.fil[0]["coeffs"].extend(list(np.zeros(nrows, dtype = 'float64')))
        else:
            z = np.zeros((ncols, nrows), dtype = 'float64')
            fb.fil[0]["coeffs"] = np.hstack((fb.fil[0]["coeffs"],z))

        self.showCoeffs()
#        self.updateCoeffs()

    def clearTable(self):
        """
        Clear table & initialize coeff, zpk for two poles and zeros @ origin
        """
        self.tblCoeff.clear()
        if self.chkIIR.isChecked():
            fb.fil[0]['coeffs'] = ([1.,0.,0.],[1.,0.,0.])
        else:
            fb.fil[0]['coeffs'] = [1.,0.,0.]
        fb.fil[0]['zpk'] = ([0.,0.],[0.,0.], 1.)

        self.showCoeffs()

    def setCoeffsZero(self):
        """
        Set all coefficients = 0 in table with a magnitude less than eps
        """
        eps = float(self.ledSetEps.text())
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        for col in range(num_cols):
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if abs(simple_eval(item.text())) < eps:
                    item.setText(str(0.))
        
    def updateCoeffs(self):
        """
        When coefficients have been edited by hand (not by another routine),
        - save coefficients, zpk, ...
        - emit the signal coeffsChanged
        """
        self.saveCoeffs()
        self.coeffsChanged.emit()  # ->pyFDA -> pltAll.updateAll()     

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputCoeffs()
    form.show()

    app.exec_()