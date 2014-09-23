# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Julia Beike, Christian Muenker
"""


import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL
import scipy.io
import numpy

from inputWidgets import ChooseParams, design_selector
from plotWidgets import plotAll


class pyFDA(QtGui.QWidget):
    PLT_SAME_WINDOW =  True
    """
    Create the main window for entering the filter specifications
    """
    def __init__(self):
        super(pyFDA, self).__init__()        
        self.initUI()     
        
    def initUI(self): 
        """
        Intitialize the main GUI, consisting of
        - Subwindow with parameter selection [ChooseParams]
        - Filter Design button 
        - Plot Window [plotterHf]
        """

        self.coeffs = (1,1) # initialize filter coefficients
        self.widgetPara = ChooseParams.ChooseParams()
#        self.widgetPara.setMaximumWidth(250)
        self.butDesignFilt = QtGui.QPushButton("DESIGN FILTER", self)
        self.butExportML = QtGui.QPushButton("Export -> ML", self)
        self.butExportCSV = QtGui.QPushButton("Export -> CSV", self)
        self.pltAll = plotAll.plotAll((1,1)) # instantiate tabbed plot widgets        
        # ============== UI Layout =====================================
        self.grLayout = QtGui.QGridLayout()
        self.grLayout.addWidget(self.widgetPara,0,0) # parameter entry widget
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
        self.connect(self.butDesignFilt, SIGNAL('clicked()'),
                     self.startDesignFilt)
        self.connect(self.butExportML, SIGNAL('clicked()'),
                     self.exportML)
        self.connect(self.butExportCSV, SIGNAL('clicked()'),
                     self.exportCSV)
        

    def startDesignFilt(self):
        """
        Design Filter
        """

        a = self.widgetPara.get()
        print "-------------------------"
        print "-------------------------"
        print a
        print "-------------------------"
        print "-------------------------"
        
        self.coeffs = design_selector.select(a)
        print self.coeffs[0]

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
        
        scipy.io.savemat('d:/Daten/filt_coeffs.mat', mdict={'filt_coeffs': self.coeffs})
        
    def exportCSV(self):
        """
        Export filter coefficients to a CSV-file 
        """
        
        numpy.savetxt('d:/Daten/filt_coeffs.csv', self.coeffs)


   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = pyFDA()
    form.show()
   
    app.exec_()