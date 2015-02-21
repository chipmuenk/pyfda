# -*- coding: utf-8 -*-
"""
Created on Jan 5th 

@author: Christian Muenker

Tabbed container for input widgets
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui

# add main directory from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import input_specs, input_files, input_info

class InputAll(QtGui.QWidget):
    """
    Create a tabbed widget for various input subwidgets
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputAll, self).__init__()


#        self.inputParams = inputParams.inputParams()
        self.inputSpecs = input_specs.InputSpecs(DEBUG = False)        
        self.inputFiles = input_files.InputFiles(DEBUG = False)
        self.inputInfo = input_info.InputInfo(DEBUG = False)
        
        self.initUI()     

        
    def initUI(self):
        """ Initialize UI with tabbed subplots """
        tabWidget = QtGui.QTabWidget()
#        tab_widget.addTab(self.inputParams, 'Params')
        tabWidget.addTab(self.inputSpecs, 'Specs')
        tabWidget.addTab(self.inputFiles, 'Files')
        tabWidget.addTab(self.inputInfo, 'Info')

        layVMain = QtGui.QVBoxLayout()
        layVMain.addWidget(tabWidget)
#        
        self.setLayout(layVMain)
#        layVMain.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        tabWidget.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Expanding)

        
#    def update(self):
#        """ Update and redraw all subplots with new coefficients"""
#        self.pltHf.draw()
#        self.pltPhi.draw()
##        self.redrawAll()

     

#------------------------------------------------------------------------
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = InputAll()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()


