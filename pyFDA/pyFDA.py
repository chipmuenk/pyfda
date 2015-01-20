# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Julia Beike, Christian Muenker

Main file for the pyFDA app, initializes UI
"""
from __future__ import print_function, division, unicode_literals
import sys
from PyQt4 import QtGui

#import filterbroker as fb # importing filterbroker initializes all its globals
from inputWidgets import input_all
from plotWidgets import plot_all


class pyFDA(QtGui.QWidget):
    PLT_SAME_WINDOW =  True
    """
    Create the main window for entering the filter specifications
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(pyFDA, self).__init__()
        # read directory with filterDesigns and construct filter tree from it
#        self.ffr = FilterFileReader('Init.txt', 'filterDesign', 
#                                    commentChar = '#', DEBUG = DEBUG) # 
        
        #self.em = QtGui.QFontMetricsF(QtGui.QLineEdit.font()).width('m')

        self.initUI()     
        
    def initUI(self): 
        """
        Intitialize the main GUI, consisting of:
        - Subwindow for parameter selection [-> ChooseParams.ChooseParams()]
        - Filter Design button [-> self.startDesignFilt()] 
        - Plot Window [-> plotAll.plotAll()]
        """

        self.inputAll = input_all.InputAll()
        self.pltAll = plot_all.plotAll() # instantiate tabbed plot widgets  
#        self.inputAll.setMaximumWidth(280)

        # ============== UI Layout =====================================

        hbox = QtGui.QHBoxLayout()

        if self.PLT_SAME_WINDOW:
            # Plot window docked in same window:
            hbox.addWidget(self.inputAll)
            hbox.addWidget(self.pltAll)

        self.setLayout(hbox)
        
        # ============== Signals & Slots ================================
#        self.butDesignFilt.clicked.connect(self.startDesignFilt)
        self.inputAll.inputParams.butDesignFilt.clicked.connect(self.pltAll.update)

#------------------------------------------------------------------------------
   
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = pyFDA()
    form.show()
   
    app.exec_()