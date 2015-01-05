# -*- coding: utf-8 -*-
"""
Created on Jan 5th 

@author: Christian Muenker

Tabbed container for input widgets
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
#from PyQt4.QtCore import SIGNAL
import scipy.io
import numpy as np

# import databroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import databroker as db # importing databroker initializes all its globals
from inputWidgets import ChooseParams, inputFiles#, inputParams
from plotWidgets import plotAll


class inputAll(QtGui.QWidget):
    """
    Create the tabbed window for various input widgets
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(inputAll, self).__init__()


#        self.inputParams = inputParams.inputParams()
        self.inputParams = ChooseParams.ChooseParams()        
        self.inputFiles = inputFiles.inputFiles()
        
        self.initUI()     

        
    def initUI(self):
        """ Initialize UI with tabbed subplots """
        tab_widget = QtGui.QTabWidget()
#        tab_widget.addTab(self.inputParams, 'Params')
        tab_widget.addTab(self.inputParams, 'Params')
        tab_widget.addTab(self.inputFiles, 'Files')

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(tab_widget)
#        
        self.setLayout(vbox)

        
#    def update(self):
#        """ Update and redraw all subplots with new coefficients"""
#        self.pltHf.draw()
#        self.pltPhi.draw()
##        self.redrawAll()

     

#------------------------------------------------------------------------
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = inputAll()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()


