# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter coefficients
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
#import scipy.io
import numpy as np
from scipy.signal import tf2zpk
from simpleeval import simple_eval

# https://github.com/danthedeckie/simpleeval

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb # importing filterbroker initializes all its globals

# TODO: drag & drop doesn't work
# TODO: selecting and deleting non-adjacent rows deletes the wrong rows
# TODO: insert row above currently selected row instead of appending at the end
# TODO: Add quantizer widget
# TODO: eliminate trailing zeros for filter order calculation
# TODO: IIR button functionality not yet implemented
class InputCoeffs(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputCoeffs, self).__init__()

        self.initUI()
        self.showCoeffs()

    def initUI(self):
        """
        Intitialize the widget, consisting of:
        -
        -
        """
        # widget / subwindow for coefficient display / entry

        self.chkCoeffList =  QtGui.QCheckBox()
        self.chkCoeffList.setChecked(True)
        self.chkCoeffList.setToolTip("Show filter coefficients as an editable list.")
        self.lblCoeffList = QtGui.QLabel()
        self.lblCoeffList.setText("Show Coefficients")

        self.chkIIR =  QtGui.QCheckBox()
        self.chkIIR.setChecked(True)
        self.chkIIR.setToolTip("IIR Filter")
        self.chkIIR.setCheckable(False) # not implemented yet
        self.chkIIR.setEnabled(False) # not implemented yet        
        self.lblIIR = QtGui.QLabel()
        self.lblIIR.setText("IIR")
        self.lblIIR.setEnabled(False) # not implemented yet 


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
        self.butDelRow.setToolTip("Delete selected row(s) from coefficient table.")
        self.butDelRow.setText("Delete")

        self.butClear = QtGui.QPushButton()
        self.butClear.setToolTip("Clear all entries.")
        self.butClear.setText("Clear")

        self.butUpdate = QtGui.QPushButton()
        self.butUpdate.setToolTip("Update filter info and plots.")
        self.butUpdate.setText("Update")

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
        self.layHButtonsCoeffs1.addWidget(self.butUpdate)
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

        # ============== Signals & Slots ================================
#        self.tblCoeff.itemEntered.connect(self.saveCoeffs) # nothing happens
#        self.tblCoeff.itemActivated.connect(self.saveCoeffs) # nothing happens
        self.tblCoeff.itemChanged.connect(self.saveCoeffs) # works but fires multiple times
        self.tblCoeff.selectionModel().currentChanged.connect(self.saveCoeffs)

        self.chkCoeffList.clicked.connect(self.showCoeffs)

        self.butDelRow.clicked.connect(self.deleteRows)
        self.butAddRow.clicked.connect(self.addRows)
        self.butClear.clicked.connect(self.clearTable)
        self.butUpdate.clicked.connect(self.showCoeffs)

        self.butSetZero.clicked.connect(self.setCoeffsZero)

    def clearTable(self):
        """
        Clear table
        """
        self.tblCoeff.clear()
        self.saveCoeffs()

    def saveCoeffs(self):
        """
        Read out table and save the values to the filter coeff dict
        """
        coeffs = []
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        if self.DEBUG: print(num_rows, num_cols)
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
            col = 0
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if item:
                    if item.text() != "":
                        coeffs.append(simple_eval(item.text()))
                else:
                    coeffs.append(0.)

#                coeffs.append(simple_eval(item.text()) if item else 0.)

        fb.fil[0]['coeffs'] = coeffs
        if np.ndim(coeffs) == 1:
            fb.fil[0]["zpk"] = tf2zpk(coeffs, 1)
        else:
            fb.fil[0]["zpk"] = tf2zpk(coeffs[0], coeffs[1]) # convert to poles / zeros
            
        fb.fil[0]["N"] = num_rows-1

        if self.DEBUG: print ("coeffs updated!")
#        self.showCoeffs()

    def showCoeffs(self):
        """
        Create table from filter coeff dict
        """
        coeffs = fb.fil[0]["coeffs"]
        self.tblCoeff.setVisible(self.chkCoeffList.isChecked())

        self.tblCoeff.setRowCount(max(np.shape(coeffs)))

        if self.DEBUG:
            print("=====================\nInputInfo.showCoeffs")
            print("Coeffs:\n",coeffs)
            print ("shape", np.shape(coeffs))
            print ("len", len(coeffs))
            print("ndim", np.ndim(coeffs))

        if np.ndim(coeffs) == 1: # FIR
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
        # returns index to rows where _all_ columns are selected
        rows = self.tblCoeff.selectionModel().selectedRows()
        rows = rows[::-1] # revert order of rows to delete from bottom
        for r in rows:
            self.tblCoeff.removeRow(r.row())
        self.saveCoeffs()

    def addRows(self):
        nrows = len(self.tblCoeff.selectionModel().selectedRows())
        if nrows == 0:
            nrows = 1 # add at least one row
        ncols = self.tblCoeff.columnCount()

        if ncols == 1: # FIR
            fb.fil[0]["coeffs"].extend(list(np.zeros(nrows)))
        else:
            z = np.zeros((ncols, nrows))
            fb.fil[0]["coeffs"] = np.hstack((fb.fil[0]["coeffs"],z))

        self.showCoeffs()

    def setCoeffsZero(self):
        """
        Set all coefficients = 0 with a magnitude less than eps
        """
        eps = float(self.ledSetEps.text())
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        for col in range(num_cols):
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if abs(simple_eval(item.text())) < eps:
                    item.setText(str(0.))
        self.saveCoeffs()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputCoeffs()
    form.show()

    app.exec_()