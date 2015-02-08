# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for exporting / importing and saving / loading data
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
import scipy.io
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
        self.labFilterInfo = QtGui.QLabel()
        self.labFilterInfo.setText("Filter Info")

        self.chkCoeffList =  QtGui.QCheckBox()
        self.chkCoeffList.setToolTip("Show filter coefficients as an editable list.")
        self.labCoeffList = QtGui.QLabel()
        self.labCoeffList.setText("Coefficients")

        self.chkPoleZeroList =  QtGui.QCheckBox()
        self.chkPoleZeroList.setToolTip("Show poles and zeros as an editable list.")
        self.labPoleZeroList = QtGui.QLabel()
        self.labPoleZeroList.setText("Poles / Zeros")
        
        self.listCoeff = QtGui.QListWidget()
        
        self.labFiltInfo = QtGui.QLabel()
        self.labFiltInfo.setWordWrap(True)
        
        filtInfoLayout = QtGui.QVBoxLayout()
        filtInfoLayout.addWidget(self.labFiltInfo)
        
        self.filtInfoFrame = QtGui.QFrame()
        self.filtInfoFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.filtInfoFrame.setLayout(filtInfoLayout)
        self.filtInfoFrame.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Minimum)


 
        # ============== UI Layout =====================================
        self.chkLayout = QtGui.QHBoxLayout()
        self.chkLayout.addWidget(self.chkFilterInfo) # filter export button
        self.chkLayout.addWidget(self.labFilterInfo)
        self.chkLayout.addStretch(1)
        self.chkLayout.addWidget(self.chkCoeffList)
        self.chkLayout.addWidget(self.labCoeffList)
        self.chkLayout.addStretch(1)        
        self.chkLayout.addWidget(self.chkPoleZeroList)
        self.chkLayout.addWidget(self.labPoleZeroList)
        self.chkLayout.addStretch(10)


        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(self.chkLayout)
        vbox.addWidget(self.listCoeff)
        vbox.addWidget(self.filtInfoFrame)
        vbox.addStretch(10)
        self.setLayout(vbox)
        
        # ============== Signals & Slots ================================
        self.chkFilterInfo.clicked.connect(self.showInfo)
        self.chkCoeffList.clicked.connect(self.showCoeffs)        

        
    def showInfo(self):
        """
        Display info from filter design file
        """
        self.filtInfoFrame.setVisible(self.chkFilterInfo.isChecked())
        self.labFiltInfo.setText(fb.gD["selFilter"]["inst"].info)
    
    def showCoeffs(self):
        self.listCoeff.setVisible(self.chkCoeffList.isChecked())
        self.listCoeff.clear()
        coeffs = fb.gD["selFilter"]["coeffs"]
        print(coeffs)
        print ("shape", np.shape(coeffs))
        print ("len", len(coeffs))
        print("ndim", np.ndim(coeffs))
        aCoeffs = []
        bCoeffs = []
        if np.ndim(coeffs) == 1:
            print("FIR!")
            for i in range(len(coeffs)):
                print(i, fb.gD["selFilter"]["coeffs"][i])
                bCoeffs.append(str(coeffs[i]))
            self.listCoeff.addItems(bCoeffs)
            print(bCoeffs)
        else:
            print("IIR!")
            for i in range(np.shape(coeffs)[1]):
                print(i, fb.gD["selFilter"]["coeffs"][0][i])
                bCoeffs.append(str(coeffs[0][i]))
                aCoeffs.append(str(coeffs[1][i]))
            self.listCoeff.addItems(bCoeffs)
#            self.listCoeff.addItems(bCoeffs)
            print(bCoeffs)


#------------------------------------------------------------------------------
   
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputInfo()
    form.show()
   
    app.exec_()