# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Julia Beike, Christian Muenker

Main file for the pyFDA app, initializes UI
"""


import sys
from PyQt4 import QtGui, QtCore
#from PyQt4.QtCore import SIGNAL
import scipy.io
import numpy

from inputWidgets import ChooseParams, design_selector
from filterDesign import cheby1
from plotWidgets import plotAll


class pyFDA(QtGui.QWidget):
    PLT_SAME_WINDOW =  True
    """
    Create the main window for entering the filter specifications
    """
    def __init__(self):
        super(pyFDA, self).__init__()
        self.coeffs = ([1,-1],[2,0]) # initialize filter coefficients a, b
        self.myFilter = cheby1.cheby1()
        self.initUI()     
        
    def initUI(self): 
        """
        Intitialize the main GUI, consisting of
        - Subwindow for parameter selection [-> ChooseParams.ChooseParams()]
        - Filter Design button [-> self.startDesignFilt] 
        - Plot Window [-> plotAll.plotAll(a,b)]
        """


        # widget / subwindow for parameter selection
        self.widgetParams = ChooseParams.ChooseParams() 
#        self.widgetPara.setMaximumWidth(250)
        self.butDesignFilt = QtGui.QPushButton("DESIGN FILTER", self)
        self.butExportML = QtGui.QPushButton("Export -> ML", self)
        self.butExportCSV = QtGui.QPushButton("Export -> CSV", self)
        self.pltAll = plotAll.plotAll(self.coeffs) # instantiate tabbed plot widgets        
        # ============== UI Layout =====================================
        self.grLayout = QtGui.QGridLayout()
        self.grLayout.addWidget(self.widgetParams,0,0) # parameter select widget
        self.grLayout.addWidget(self.butDesignFilt,1,0) # filter design button
        self.grLayout.addWidget(self.butExportML,2,0) # filter export button
        self.grLayout.addWidget(self.butExportCSV,3,0) # filter export button


        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(self.grLayout)
#        hbox.addWidget(self.pltAll)

        if self.PLT_SAME_WINDOW:
            # Plot window docked in same window:
#            self.layout.addWidget(self.pltAll,0,1) 
            hbox.addWidget(self.pltAll) 
        self.setLayout(hbox)
#        self.setLayout(self.layout)
        # ============== Signals & Slots ================================

        self.butDesignFilt.clicked.connect(self.startDesignFilt)
        self.butExportML.clicked.connect(self.exportML)
        self.butExportCSV.clicked.connect(self.exportCSV)        

    def startDesignFilt(self):
        """
        Design Filter
        """

        params = self.widgetParams.get()
        print "-------------------------"
        print "-------------------------"
        print params
        print "-------------------------"
        print "-------------------------"
        
        self.myFilter.LP(params) # design filter
        self.coeffs = self.myFilter.coeff # and read back coefficients

        print self.coeffs

        if self.PLT_SAME_WINDOW:       
            self.pltAll.update(self.coeffs)
        else:
            # Separate window for plots:
            self.pltAll.update(self.coeffs)
            self.pltAll.show()

        
    def exportML(self):
        """
        Export filter coefficients to a file that can be imported into 
        Matlab workspace
        """
        
        scipy.io.savemat('d:/Daten/filt_coeffs.mat', 
                         mdict={'filt_coeffs': self.coeffs})
        print("exportML: Matlab workspace exported!")
        
    def exportCSV(self):
        """
        Export filter coefficients to a CSV-file 
        """
        
        numpy.savetxt('d:/Daten/filt_coeffs.csv', self.coeffs)
        print("exportCSV: CSV - File exported!")
#------------------------------------------------------------------------------
   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = pyFDA()
    form.show()
   
    app.exec_()