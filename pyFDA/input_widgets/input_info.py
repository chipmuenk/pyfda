# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for exporting / importing and saving / loading data
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
#import scipy.io
import numpy as np

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb # importing filterbroker initializes all its globals


class InputInfo(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputInfo, self).__init__()

        self.initUI()
        self.showCoeffs()
        self.showInfo()
        
    def initUI(self): 
        """
        Intitialize the widget, consisting of:
        - 
        - 
        """
        # widget / subwindow for parameter selection
        self.chkFilterInfo = QtGui.QCheckBox()
        self.chkFilterInfo.setToolTip("Display filter info from filter design file.")
        self.lblFilterInfo = QtGui.QLabel()
        self.lblFilterInfo.setText("Filter Info")

        self.chkCoeffList =  QtGui.QCheckBox()
        self.chkCoeffList.setToolTip("Show filter coefficients as an editable list.")
        self.lblCoeffList = QtGui.QLabel()
        self.lblCoeffList.setText("Coefficients")

        self.chkPoleZeroList =  QtGui.QCheckBox()
        self.chkPoleZeroList.setToolTip("Show poles and zeros as an editable list.")
        self.lblPoleZeroList = QtGui.QLabel()
        self.lblPoleZeroList.setText("Poles / Zeros")
        
        self.tblCoeff = QtGui.QTableWidget()
        self.tblCoeff.setEditTriggers(QtGui.QTableWidget.AllEditTriggers)
        self.tblCoeff.setAlternatingRowColors(True)
#        self.tblCoeff.itemEntered.connect(self.saveCoeffs) # nothing happens
#        self.tblCoeff.itemActivated.connect(self.saveCoeffs) # nothing happens
        self.tblCoeff.itemChanged.connect(self.saveCoeffs) # works but fires multiple times
        self.butAddRow = QtGui.QPushButton()
        self.butAddRow.setToolTip("Add row to coefficient table.")
        self.butAddRow.setText("Add")
        
        self.butDelRow = QtGui.QPushButton()
        self.butDelRow.setToolTip("Delete row from coefficient table.")
        self.butDelRow.setText("Delete")

        
        self.lblFiltInfo = QtGui.QLabel()
        self.lblFiltInfo.setWordWrap(True)
        
        filtInfoLayout = QtGui.QVBoxLayout()
        filtInfoLayout.addWidget(self.lblFiltInfo)
        
        self.frmFiltInfo = QtGui.QFrame()
        self.frmFiltInfo.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.frmFiltInfo.setLayout(filtInfoLayout)
        self.frmFiltInfo.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Minimum)


 
        # ============== UI Layout =====================================
        self.chkLayout = QtGui.QHBoxLayout()
        self.chkLayout.addWidget(self.chkFilterInfo) # filter export button
        self.chkLayout.addWidget(self.lblFilterInfo)
        self.chkLayout.addStretch(1)
        self.chkLayout.addWidget(self.chkCoeffList)
        self.chkLayout.addWidget(self.lblCoeffList)
        self.chkLayout.addStretch(1)        
        self.chkLayout.addWidget(self.chkPoleZeroList)
        self.chkLayout.addWidget(self.lblPoleZeroList)
        self.chkLayout.addStretch(10)
        
        self.butCoeffLayout = QtGui.QHBoxLayout()
        self.butCoeffLayout.addWidget(self.butAddRow)
        self.butCoeffLayout.addWidget(self.butDelRow)
        self.butCoeffLayout.addStretch()


        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(self.chkLayout)
        vbox.addWidget(self.tblCoeff)
        vbox.addLayout(self.butCoeffLayout)
        vbox.addWidget(self.frmFiltInfo)
        vbox.addStretch(10)
        self.setLayout(vbox)
        
        # ============== Signals & Slots ================================
        self.chkFilterInfo.clicked.connect(self.showInfo)
        self.chkCoeffList.clicked.connect(self.showCoeffs)        

        
    def showInfo(self):
        """
        Display info from filter design file
        """
        self.frmFiltInfo.setVisible(self.chkFilterInfo.isChecked())
        try:
            self.lblFiltInfo.setText(fb.filObj.info)
        except AttributeError as e:
            print(e)
    
        
    def saveCoeffs(self):
        coeffs = []
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        print(num_rows, num_cols)
        if num_cols > 1:
            for col in range(num_cols):
                rows = []
                for row in range(num_rows):
                    item = self.tblCoeff.item(row, col)
                    rows.append(float(item.text()) if item else 0.)
                coeffs.append(rows)
        else:
            col = 0
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                coeffs.append(float(item.text()) if item else 0.)            
        
        fb.fil[0]['coeffs'] = coeffs
        print ("coeffs updated!")
        
    def showCoeffs(self):
            
        coeffs = fb.fil[0]["coeffs"]
        self.tblCoeff.setVisible(self.chkCoeffList.isChecked())

        self.tblCoeff.clear()
        self.tblCoeff.setRowCount(max(np.shape(coeffs)))


        if self.DEBUG:
            print("=====================\nInputInfo.showCoeffs")
            print("Coeffs:\n",coeffs)
            print ("shape", np.shape(coeffs))
            print ("len", len(coeffs))
            print("ndim", np.ndim(coeffs))
            
#        if np.ndim(fb.fil[0]['coeffs']) == 1: # FIR
#            self.bb = fb.fil[0]['coeffs']
#            self.aa = 1.
#        else: # IIR
#            self.bb = fb.fil[0]['coeffs'][0]
#            self.aa = fb.fil[0]['coeffs'][1]

        if np.ndim(coeffs) == 1:
            print("FIR!")
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])
            for i in range(len(coeffs)):
                print(i, coeffs[i])
                item = QtGui.QTableWidgetItem(str(coeffs[i]))
                self.tblCoeff.setItem(i,0,item)
        else:
            print("IIR!")
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
            for i in range(np.shape(coeffs)[1]):
#                print(i, fb.fil[0]["coeffs"][0][i])
#                item = QtGui.QTableWidgetItem(coeffs[0][i])
#                bCoeffs.append(str(coeffs[0][i]))
#                aCoeffs.append(str(coeffs[1][i]))
                self.tblCoeff.setItem(i,0,QtGui.QTableWidgetItem(str(coeffs[0][i])))
                self.tblCoeff.setItem(i,1,QtGui.QTableWidgetItem(str(coeffs[1][i])))

        self.tblCoeff.resizeColumnsToContents()



#------------------------------------------------------------------------------
   
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputInfo()
    form.show()
   
    app.exec_()