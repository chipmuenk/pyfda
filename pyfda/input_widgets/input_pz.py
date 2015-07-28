# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter Poles and Zeros
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal
import numpy as np
from scipy.signal import freqz

# https://github.com/danthedeckie/simpleeval

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import cround, save_fil
from pyfda.simpleeval import simple_eval

# TODO: delete / insert individual cells instead of rows
# TODO: correct scaling after insertion / deletion of cells
# TODO: drag & drop doesn't work
# TODO: insert row above currently selected row instead of appending at the end
# TODO: eliminate trailing zeros for filter order calculation


class InputPZ(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputPZ, self).__init__()

        self.initUI()

    def initUI(self):
        """
        Intitialize the widget, consisting of:
        """
        
        # Find which button holds the longest text:
        MaxTextlen = 0
        longestText = ""
        ButLength = 0
        butTexts = ["Add", "Delete", "Save", "Load", "Clear", "Set Zero"]
        
        for item in butTexts:
            if len(item) > MaxTextlen:
                MaxTextlen = len(item)
                longestText = item        

        self.chkPZList =  QtGui.QCheckBox()
        self.chkPZList.setChecked(True)
        self.chkPZList.setToolTip("Show filter Poles / Zeros as an editable list.")
        self.chkPZList.setText("Show Poles / Zeros")

        self.lblRound = QtGui.QLabel("Digits = ")
        self.spnRound = QtGui.QSpinBox()
        self.spnRound.setRange(0,9)
        self.spnRound.setValue(0)
        self.spnRound.setToolTip("Round to d digits.")

        self.lblGain = QtGui.QLabel("k = ")
        
        self.chkNorm =  QtGui.QCheckBox()
        self.chkNorm.setChecked(True)
        self.chkNorm.setToolTip("Normalize max. (H(f)).")
        self.chkNorm.setText("Normalize")

        self.ledGain = QtGui.QLineEdit()
        self.ledGain.setToolTip("Specify gain factor k.")
        self.ledGain.setText(str(1.))

        self.tblPZ = QtGui.QTableWidget()
        self.tblPZ.setEditTriggers(QtGui.QTableWidget.AllEditTriggers)
        self.tblPZ.setAlternatingRowColors(True)
        self.tblPZ.setDragEnabled(True)
        self.tblPZ.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.tblPZ.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                          QtGui.QSizePolicy.Expanding)

        self.butAddRow = QtGui.QPushButton()
        self.butAddRow.setToolTip("Add row to PZ table.\n"
                                "Select n existing rows to append n new rows.")
        self.butAddRow.setText(butTexts[0])
        
        ButLength = self.butAddRow.fontMetrics().boundingRect(longestText).width()+10
        self.butAddRow.setMaximumWidth(ButLength)

        self.butDelRow = QtGui.QPushButton()
        self.butDelRow.setToolTip("Delete selected row(s) from the table.\n"
                "Multiple rows can be selected using <SHIFT> or <CTRL>."
                "If nothing is selected, delete last row.")
        self.butDelRow.setText(butTexts[1])
        self.butDelRow.setMaximumWidth(ButLength)

        self.butClear = QtGui.QPushButton()
        self.butClear.setToolTip("Clear all entries.")
        self.butClear.setText(butTexts[4])
        self.butClear.setMaximumWidth(ButLength)              

        self.butSave = QtGui.QPushButton()
        self.butSave.setToolTip("Save P/Z & update all plots.\n"
                                "No modifications are saved before!")
        self.butSave.setText(butTexts[2])
        self.butSave.setMaximumWidth(ButLength)

        self.butLoad = QtGui.QPushButton()
        self.butLoad.setToolTip("Reload P / Z.")
        self.butLoad.setText(butTexts[3])
        self.butLoad.setMaximumWidth(ButLength)              

        self.butSetZero = QtGui.QPushButton()
        self.butSetZero.setToolTip("Set P / Z = 0 with a magnitude < eps.")
        self.butSetZero.setText(butTexts[5])
        self.butSetZero.setMaximumWidth(ButLength)              

        self.lblEps = QtGui.QLabel("for P, Z <")

        self.ledSetEps = QtGui.QLineEdit()
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        # ============== UI Layout =====================================
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkPZList)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblRound)
        self.layHChkBoxes.addWidget(self.spnRound)

        self.layHGain = QtGui.QHBoxLayout()
        self.layHGain.addWidget(self.lblGain)
        self.layHGain.addWidget(self.ledGain)
        self.layHChkBoxes.addStretch(1)
        self.layHGain.addWidget(self.chkNorm)
        self.layHGain.addStretch()

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
#        layVMain.addStretch(1)
        self.setLayout(layVMain)
        
        self.showZPK() # initialize table with default values from filterbroker

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
#        self.tblPZ.itemEntered.connect(self.saveZPK) # nothing happens
#        self.tblPZ.itemActivated.connect(self.saveZPK) # nothing happens
#        self.tblPZ.itemChanged.connect(self.saveZPK) # works but fires multiple times
#        self.tblPZ.selectionModel().currentChanged.connect(self.saveZPK)
#        self.tblPZ.clicked.connect(self.saveZPK)
#        self.ledGain.editingFinished.connect(self.saveZPK)

        self.spnRound.editingFinished.connect(self.showZPK)
        self.butLoad.clicked.connect(self.showZPK)
        self.chkPZList.clicked.connect(self.showZPK)

        self.butSave.clicked.connect(self.saveZPK)

        self.butDelRow.clicked.connect(self.deleteRows)
        self.butAddRow.clicked.connect(self.addRows)
        self.butClear.clicked.connect(self.clearTable)

        self.butSetZero.clicked.connect(self.setZPKZero)
        #----------------------------------------------------------------------


    def clearTable(self):
        """
        Clear & initialize table for two poles and zeros @ origin,
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

        #iterate over both columns
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

        zpk.append(simple_eval(self.ledGain.text())) # append k factor to zpk

        fb.fil[0]["N"] = num_rows
        save_fil(fb.fil[0], zpk, 'zpk', __name__) # save & convert to 'ba'
        
        if self.chkNorm.isChecked():
            # set gain factor k (zpk[2]) in such a way that the max. filter 
            # gain remains unchanged
            [w, H] = freqz(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1]) # (bb, aa)
            zpk[2] = zpk[2] * self.Hmax_last / max(abs(H))
            save_fil(fb.fil[0], zpk, 'zpk', __name__) # save with new gain '

        if __name__ == '__main__':
            self.showZPK() # only needed for stand-alone test
            
        self.sigFilterDesigned.emit()

        if self.DEBUG:
            print("ZPK - coeffs:",  fb.fil[0]['ba'])
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
        
        if self.chkNorm.isChecked():
            [w, H] = freqz(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1]) # (bb, aa)
            self.Hmax_last = max(abs(H)) # store current max. filter gain

        self.ledGain.setText(str(cround(zpk[2], n_digits)))

        self.tblPZ.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setRowCount(max(len(zpk[0]),len(zpk[1])))

        if self.DEBUG:
            print("=====================\nInputPZ.showZPK")
            print("ZPK:\n",zpk)
            print ("shape", np.shape(zpk))
            print ("len", len(zpk))
            print("ndim", np.ndim(zpk))

        self.tblPZ.setColumnCount(2)
        self.tblPZ.setHorizontalHeaderLabels(["Z", "P"])
        for col in range(2):
            for row in range(len(zpk[col])):
                if self.DEBUG: print("Len Row:", len(zpk[col]))
                item = self.tblPZ.item(row, col)
                # copy content of zpk to corresponding table field, rounding 
                # as specified and removing the brackets of complex arguments
                if item: # does item exist?
                    item.setText(str(cround(zpk[col][row], n_digits)).strip('()'))
                else: # no construct it
                    self.tblPZ.setItem(row,col,QtGui.QTableWidgetItem(
                          str(cround(zpk[col][row], n_digits)).strip('()')))

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