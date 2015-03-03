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
# TODO: selecting and deleting non-adjacent rows deletes the wrong rows
# TODO: insert row above currently selected row instead of appending at the end
# TODO: Add quantizer widget
# TODO: eliminate trailing zeros for filter order calculation
# TODO: IIR button functionality not yet implemented
class InputPZ(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputPZ, self).__init__()
        
        self.ncols = 2

        self.initUI()
        self.showZPK()

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

        self.chkIIR =  QtGui.QCheckBox()
        self.chkIIR.setChecked(True)
        self.chkIIR.setToolTip("IIR Filter")
        self.chkIIR.setCheckable(False) # not implemented yet
        self.chkIIR.setEnabled(False) # not implemented yet
        self.lblIIR = QtGui.QLabel()
        self.lblIIR.setText("IIR")
        self.lblIIR.setEnabled(False) # not implemented yet

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
        self.butAddRow.setToolTip("Add row to PZ table.\nSelect n existing rows to append n new rows.")
        self.butAddRow.setText("Add")

        self.butDelRow = QtGui.QPushButton()
        self.butDelRow.setToolTip("Delete selected row(s) from the table.\n"
                "Multiple rows can be selected using <SHIFT> or <CTRL>.")
        self.butDelRow.setText("Delete")

        self.butClear = QtGui.QPushButton()
        self.butClear.setToolTip("Clear all entries.")
        self.butClear.setText("Clear")

        self.butUpdate = QtGui.QPushButton()
        self.butUpdate.setToolTip("Update filter info and plots.")
        self.butUpdate.setText("Update")

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
        self.layHChkBoxes.addWidget(self.chkIIR)
        self.layHChkBoxes.addWidget(self.lblIIR)
#        self.layHChkBoxes.addStretch(10)

        self.layHGain = QtGui.QHBoxLayout()        
        self.layHGain.addWidget(self.lblGain)
        self.layHGain.addWidget(self.ledGain)
        self.layHGain.addStretch(10)

        self.layHButtonsPZs1 = QtGui.QHBoxLayout()
        self.layHButtonsPZs1.addWidget(self.butAddRow)
        self.layHButtonsPZs1.addWidget(self.butDelRow)
        self.layHButtonsPZs1.addWidget(self.butClear)
        self.layHButtonsPZs1.addWidget(self.butUpdate)
        self.layHButtonsPZs1.addStretch()

        self.layHButtonsPZs2 = QtGui.QHBoxLayout()
        self.layHButtonsPZs2.addWidget(self.butSetZero)
        self.layHButtonsPZs2.addWidget(self.lblEps)
        self.layHButtonsPZs2.addWidget(self.ledSetEps)
        self.layHButtonsPZs2.addStretch()

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addLayout(self.layHGain)
        layVMain.addWidget(self.tblPZ)
        layVMain.addLayout(self.layHButtonsPZs1)
        layVMain.addLayout(self.layHButtonsPZs2)
#        layVMain.addStretch(1)
        self.setLayout(layVMain)

        # ============== Signals & Slots ================================
#        self.tblPZ.itemEntered.connect(self.savePZs) # nothing happens
#        self.tblPZ.itemActivated.connect(self.savePZs) # nothing happens
        self.ledGain.editingFinished.connect(self.saveZPK)
        self.tblPZ.itemChanged.connect(self.saveZPK) # works but fires multiple times
        self.tblPZ.selectionModel().currentChanged.connect(self.saveZPK)
        self.butUpdate.clicked.connect(self.saveZPK)

        self.chkPZList.clicked.connect(self.showZPK)

        self.butDelRow.clicked.connect(self.deleteRows)
        self.butAddRow.clicked.connect(self.addRows)
        self.butClear.clicked.connect(self.clearTable)


        self.butSetZero.clicked.connect(self.setZPKZero)

    def clearTable(self):
        """
        Clear table and fill P/Z with zeros
        """
        self.tblPZ.clear()
        self.saveZPK()

    def saveZPK(self):
        """
        Read out table and save the values to the filter PZ dict
        """
        zpk = []
        num_rows = self.tblPZ.rowCount()
        if self.DEBUG: print("nrows:",num_rows)

        for col in range(self.ncols):
            rows = []
            for row in range(num_rows):
                item = self.tblPZ.item(row, col)
                if item:
                    if item.text() != "":
                        rows.append(simple_eval(item.text()))
                else:
                    rows.append(0.)
#                    rows.append(float(item.text()) if item else 0.)
            zpk.append(rows)
            
        zpk.append([float(self.ledGain.text())])
        
        fb.fil[0]["zpk"] = zpk

#                ZPK.append(simple_eval(item.text()) if item else 0.)

#        fb.fil[0]['ZPK'] = np.array(coeffs, dtype = 'float64')

#        fb.fil[0]["zpk"] = tf2zpk(coeffs[0], coeffs[1]) # convert to poles / zeros
#        print(coeffs)
#        fb.fil[0]["N"] = num_rows-1
#        print( fb.fil[0]["zpk"])

        if self.DEBUG: print ("zpk updated!")

    def showZPK(self):
        """
        Create table from filter zpk dict
        """
        zpk = fb.fil[0]["zpk"]
        self.tblPZ.setVisible(self.chkPZList.isChecked())

        self.tblPZ.setRowCount(max(len(zpk[0]),len(zpk[1])))

        if self.DEBUG:
            print("=====================\nInputInfo.showZPK")
            print("ZPK:\n",zpk)
            print ("shape", np.shape(zpk))
            print ("len", len(zpk))
            print("ndim", np.ndim(zpk))

   

        self.tblPZ.setColumnCount(2)
        self.tblPZ.setHorizontalHeaderLabels(["z", "p"])
        for col in range(self.ncols):
            for row in range(len(zpk[col])):
                if self.DEBUG:print("Len Row:", len(zpk[col]))
                item = self.tblPZ.item(row, col)
                if item:
                    item.setText(str(zpk[col][row]))
                else:
                    self.tblPZ.setItem(row,col,QtGui.QTableWidgetItem(
                                                        str(zpk[col][row])))
        self.tblPZ.resizeColumnsToContents()
        self.tblPZ.resizeRowsToContents()
        self.ledGain.setText(str(zpk[2]))

    def deleteRows(self):
        indices = self.tblPZ.selectionModel().selectedIndexes()
        rows = set() 
        for index in indices:
            rows.add(index.row()) # collect all selected rows in a set
        rows = sorted(list(rows), reverse = True)# sort rows in decending order
        print(rows)
        for r in rows:
#            self.tblCoeff.removeRow(r.row())
            self.tblPZ.removeRow(r)
        self.saveZPK()
        
    def addRows(self):
        """
        Add the number of selected rows to the table, rows need to be fully
        selected. If nothing is selected, add 1 row. Afterwards, refresh
        the table.
        """
        nrows = len(self.tblPZ.selectionModel().selectedRows())
        if nrows == 0:
            nrows = 1 # add at least one row

        z = np.zeros((self.ncols, nrows))
        print(np.shape(z))
        print(np.shape(fb.fil[0]["zpk"]))
        fb.fil[0]["zpk"][0:1] = np.hstack((fb.fil[0]["zpk"][0:1],z))

        self.showZPK()

    def setZPKZero(self):
        """
        Set all PZs = 0 with a magnitude less than eps
        """
        eps = float(self.ledSetEps.text())
        num_rows= self.tblPZ.rowCount()
        
        for col in range(self.ncols):
            for row in range(num_rows):
                item = self.tblPZ.item(row, col)
                if abs(simple_eval(item.text())) < eps:
                    item.setText(str(0.))
        self.saveZPK()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputPZ()
    form.show()

    app.exec_()