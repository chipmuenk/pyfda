# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter coefficients
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal
#import scipy.io
import numpy as np
#from scipy.signal import tf2zpk


# https://github.com/danthedeckie/simpleeval

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb # importing filterbroker initializes all its globals
from pyfda_lib import cround, save_fil
import pyfda_lib_fix_v3 as fix
from simpleeval import simple_eval

# TODO: delete / insert individual cells instead of rows
# TODO: drag & drop doesn't work
# TODO: insert row above currently selected row instead of appending at the end
# TODO: eliminate trailing zeros for filter order calculation
# TODO: IIR button functionality not yet implemented, needed?
# TODO: Fill combobox for Wrap / Quant settings
# TODO: Fix fixpoint lib: toggling between -MSB and + MSB is wrong

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

#        self.nrows = 0 # keep track of number of rows

        self.initUI()

    def initUI(self):
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        
        """Edit WinMic"""
         #Whitch Button holds the longest Text?
        
        
#        butAddRowText = 
#        butDelRowtext = 
#        butSaveText = "Save"
#        butLoadText = "Load"
#        butClearText = "Clear"
#        butSetZeroText = "Set Zero"
#        butQuantText = "< Q >"
        MaxTextlen = 0
        longestText = ""
        ButLength = 0
        butTexts = ["Add", "Delete", "Save", "Load", "Clear", "Set Zero", "< Q >"]
        
        for item in butTexts:
            if len(item) > MaxTextlen:
                MaxTextlen = len(item)
                longestText = item        
        """End"""
        
        

        self.chkCoeffList =  QtGui.QCheckBox()
        self.chkCoeffList.setChecked(True)
        self.chkCoeffList.setToolTip("Show filter coefficients as an editable list.")
        self.lblCoeffList = QtGui.QLabel()
        self.lblCoeffList.setText("Show Coefficients")

        self.chkIIR = QtGui.QCheckBox()
        self.chkIIR.setChecked(True)
        self.chkIIR.setToolTip("IIR Filter")
#        self.chkIIR.setCheckable(False) # not implemented yet
#        self.chkIIR.setEnabled(False) # not implemented yet
        self.lblIIR = QtGui.QLabel()
        self.lblIIR.setText("IIR")

        self.tblCoeff = QtGui.QTableWidget()
        self.tblCoeff.setEditTriggers(QtGui.QTableWidget.AllEditTriggers)
        self.tblCoeff.setAlternatingRowColors(True)
#        self.tblCoeff.QItemSelectionModel.Clear
        self.tblCoeff.setDragEnabled(True)
        self.tblCoeff.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.tblCoeff.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                          QtGui.QSizePolicy.MinimumExpanding)

        self.butAddRow = QtGui.QPushButton()
        self.butAddRow.setToolTip("Add row to coefficient table.\nSelect n existing rows to append n new rows.")
        
        """EDIT WinMic"""
        
        self.butAddRow.setText(butTexts[0])
        
        #Calculate the length for the Buttons based on the longest ButtonText
        ButLength = self.butAddRow.fontMetrics().boundingRect(longestText).width()+10
        self.butAddRow.setMaximumWidth(ButLength)
        """End"""

         

        self.butDelRow = QtGui.QPushButton()
        self.butDelRow.setToolTip("Delete selected row(s) from the table.\n"
                "Multiple rows can be selected using <SHIFT> or <CTRL>.\n"
                "When noting is selected, delete last row.")
        self.butDelRow.setText(butTexts[1])
        self.butDelRow.setMaximumWidth(ButLength)

        self.butSave = QtGui.QPushButton()
        self.butSave.setToolTip("Save coefficients & update filter plots.")
        self.butSave.setText(butTexts[2])
        self.butSave.setMaximumWidth(ButLength)

        self.butLoad = QtGui.QPushButton()
        self.butLoad.setToolTip("Reload coefficients.")
        self.butLoad.setText(butTexts[3])
        self.butLoad.setMaximumWidth(ButLength)

        self.butClear = QtGui.QPushButton()
        self.butClear.setToolTip("Clear all entries.")
        self.butClear.setText(butTexts[4])
        self.butClear.setMaximumWidth(ButLength)


        self.butSetZero = QtGui.QPushButton()
        self.butSetZero.setToolTip("Set coefficients = 0 with a magnitude < eps.")
        self.butSetZero.setText(butTexts[5])
        self.butSetZero.setMaximumWidth(ButLength)

        self.lblEps = QtGui.QLabel()
        self.lblEps.setText("for b, a <")

        self.ledSetEps = QtGui.QLineEdit()
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        self.butQuant = QtGui.QPushButton()
        self.butQuant.setToolTip("Quantize coefficients = 0 with a magnitude < eps.")
        self.butQuant.setText(butTexts[6])
        self.butQuant.setMaximumWidth(ButLength)

        self.lblQuant = QtGui.QLabel()
        self.lblQuant.setText("QI.QF = ")
        
        """EditWinMic"""
        self.lblQuantisierung = QtGui.QLabel()
        self.lblQuantisierung.setText("Koeffizientenquant. :")
        """END"""

        self.ledQuantI = QtGui.QLineEdit()
        self.ledQuantI.setToolTip("Specify number of integer bits.")
        self.ledQuantI.setText("0")
        self.ledQuantI.setMaxLength(2) # maximum of 2 digits
        self.ledQuantI.setFixedWidth(30) # width of lineedit in points(?)

        self.lblDot = QtGui.QLabel()
        self.lblDot.setText(".")

        self.ledQuantF = QtGui.QLineEdit()
        self.ledQuantF.setToolTip("Specify number of fractional bits.")
        self.ledQuantF.setText("15")
        self.ledQuantF.setMaxLength(2) # maximum of 2 digits
#        self.ledQuantF.setFixedWidth(30) # width of lineedit in points(?)
        self.ledQuantF.setMaximumWidth(30)

        self.cmbQQuant = QtGui.QComboBox()
        qQuant = ['none', 'round', 'fix']
        self.cmbQQuant.addItems(qQuant)
        self.cmbQOvfl = QtGui.QComboBox()
        qOvfl = ['none', 'wrap', 'sat']
        self.cmbQOvfl.addItems(qOvfl)
        
        """Edit WinMic"""
        #Die ComboBox passt Ihre größe dynamisch dem längsten element an.
        self.cmbQQuant.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbQOvfl.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        """END"""

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
        self.layHButtonsCoeffs1.addWidget(self.butSave)
        self.layHButtonsCoeffs1.addWidget(self.butLoad)
        self.layHButtonsCoeffs1.addStretch()

        self.layHButtonsCoeffs2 = QtGui.QHBoxLayout()
        self.layHButtonsCoeffs2.addWidget(self.butClear)
        self.layHButtonsCoeffs2.addWidget(self.butSetZero)
        self.layHButtonsCoeffs2.addWidget(self.lblEps)
        self.layHButtonsCoeffs2.addWidget(self.ledSetEps)
        self.layHButtonsCoeffs2.addStretch()

        self.layHButtonsCoeffs3 = QtGui.QHBoxLayout()
        self.layHButtonsCoeffs3.addWidget(self.butQuant)
        self.layHButtonsCoeffs3.addWidget(self.lblQuant)
        self.layHButtonsCoeffs3.addWidget(self.ledQuantI)
        self.layHButtonsCoeffs3.addWidget(self.lblDot)
        self.layHButtonsCoeffs3.addWidget(self.ledQuantF)

        self.layHButtonsCoeffs3.addStretch()
        
        """EDIT WinMic"""
        self.layHButtonsCoeffs4 = QtGui.QHBoxLayout()
        spacer = QtGui.QSpacerItem(1, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.layHButtonsCoeffs4.addWidget(self.lblQuantisierung)
        self.layHButtonsCoeffs4.addWidget(self.cmbQOvfl)
        self.layHButtonsCoeffs4.addWidget(self.cmbQQuant)
        self.layHButtonsCoeffs4.addItem(spacer)
        """END"""

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addLayout(self.layHButtonsCoeffs1)
        layVMain.addLayout(self.layHButtonsCoeffs2)
        layVMain.addLayout(self.layHButtonsCoeffs3)
        layVMain.addLayout(self.layHButtonsCoeffs4)
        layVMain.addWidget(self.tblCoeff)
        layVMain.addStretch(1)
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

        self.chkCoeffList.clicked.connect(self.showCoeffs)
        self.butLoad.clicked.connect(self.showCoeffs)

        self.butSave.clicked.connect(self.saveCoeffs)

        self.butDelRow.clicked.connect(self.deleteRows)
        self.butAddRow.clicked.connect(self.addRows)

        self.butClear.clicked.connect(self.clearTable)
        self.butSetZero.clicked.connect(self.setCoeffsZero)
        self.butQuant.clicked.connect(self.quantCoeffs)

    def saveCoeffs(self):
        """
        Read out coefficients table and save the values to filter 'coeffs'
        and 'zpk' dicts. Is called when clicking the <Save> button, triggers
        a recalculation and replot of all plot widgets.
        """
        if self.DEBUG:
            print("=====================\nInputCoeffs.saveCoeffs")
        coeffs = []
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        if self.DEBUG: print("Tbl rows /  cols:", num_rows, num_cols)
#        if num_cols > 1: # IIR
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

        fb.fil[0]["N"] = num_rows - 1
        save_fil(fb.fil[0], coeffs, 'ba', __name__)

        if self.DEBUG:
            print("Coeffs - ZPK:", fb.fil[0]["zpk"])
            print("Coeffs - IIR:", coeffs)
            print ("Coeffs updated!")

        self.coeffsChanged.emit()  # ->pyFDA -> pltAll.updateAll()

    def showCoeffs(self):
        """
        Create table from filter coeff dict
        """
        coeffs = fb.fil[0]["coeffs"]
        self.tblCoeff.setVisible(self.chkCoeffList.isChecked())

        self.tblCoeff.setRowCount(max(np.shape(coeffs)))
        self.tblCoeff.setColumnCount(2)

        if self.DEBUG:
            print("=====================\nInputCoeffs.showCoeffs")
            print("Coeffs:\n",coeffs)
            print ("shape", np.shape(coeffs))
            print ("len", len(coeffs))
            print("ndim", np.ndim(coeffs))

#        if np.ndim(coeffs) == 1: # FIR

        self.chkIIR.setChecked(True)

        self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
        for col in range(2):
            for row in range(np.shape(coeffs)[1]):
                item = self.tblCoeff.item(row, col)
                if item:
                    item.setText(str(cround(coeffs[col][row])))
                else:
                    self.tblCoeff.setItem(row,col,QtGui.QTableWidgetItem(
                                            str(cround(coeffs[col][row]))))
        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()

    def deleteRows(self):
        """
        Delete all selected rows by:
        - reading the indices of all selected cells
        - collecting the row numbers in a set (only unique elements)
        - sort the elements in a list in descending order
        - delete the rows starting at the bottom
        If nothing is selected, delete last row.
        """
        # returns index to rows:
#        rows = self.tblCoeff.selectionModel().selectedRows()
        nrows = self.tblCoeff.rowCount()
        indices = self.tblCoeff.selectionModel().selectedIndexes()
        rows = set()
        for index in indices:
            rows.add(index.row()) # collect all selected rows in a set
        if len(rows) == 0: # nothing selected
            rows = {nrows-1} # -> select last row
        rows = sorted(list(rows), reverse = True)# sort rows in decending order
        for r in rows:
#            self.tblCoeff.removeRow(r.row())
            self.tblCoeff.removeRow(r)
        self.tblCoeff.setRowCount(nrows - len(rows))

    def addRows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add 1 row.
        """
        old_rows = self.tblCoeff.rowCount()
        new_rows = len(self.tblCoeff.selectionModel().selectedRows()) + old_rows
        self.tblCoeff.setRowCount(new_rows)

        if old_rows == new_rows: # nothing selected
            new_rows = old_rows + 1 # add at least one row

        self.tblCoeff.setRowCount(new_rows)

        for col in range(2):
            for row in range(old_rows, new_rows):
                self.tblCoeff.setItem(row,col,QtGui.QTableWidgetItem("0.0"))

        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()


    def clearTable(self):
        """
        Clear table & initialize coeff, zpk for two poles and zeros @ origin,
        a = b = [1; 0; 0]
        """
        self.tblCoeff.clear()
        self.tblCoeff.setRowCount(3)

        num_cols = self.tblCoeff.columnCount()
        for row in range(3):
            for col in range(num_cols):
                if row == 0:
                    self.tblCoeff.setItem(row,col,QtGui.QTableWidgetItem("1.0"))
                else:
                    self.tblCoeff.setItem(row,col,QtGui.QTableWidgetItem("0.0"))

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
                if item:
                    if abs(simple_eval(item.text())) < eps:
                        item.setText(str(0.))
                else:
                    self.tblCoeff.setItem(row,col,QtGui.QTableWidgetItem("0.0"))

    def quantCoeffs(self):
        """
        Quantize all coefficients
        """
        qI = int(self.ledQuantI.text())
        qF = int(self.ledQuantF.text())
        qQuant = self.cmbQQuant.currentText()
        qOvfl = self.cmbQOvfl.currentText()
        q_obj =  {'QI':qI, 'QF': qF, 'quant': qQuant, 'ovfl': qOvfl}
        myQ = fix.Fixed(q_obj) # instantiate fixed-point object
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        for col in range(num_cols):
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if item:
                    item.setText(str(myQ.fix(simple_eval(item.text()))))
                else:
                    self.tblCoeff.setItem(row,col,QtGui.QTableWidgetItem("0.0"))
                    
        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputCoeffs()
    form.show()

    app.exec_()