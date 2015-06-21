# -*- coding: utf-8 -*-
"""
Created on Jan 5th

@author: Christian Muenker

Tabbed container for all input widgets
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

# add main directory from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

from input_widgets import input_specs, input_files, input_coeffs, input_info, input_pz

class InputAll(QtGui.QWidget):
    """
    Create a tabbed widget for various input subwidgets
    """
    # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal()  # emitted when specs have been changed


    def __init__(self, DEBUG = False):
        self.DEBUG = DEBUG
        super(InputAll, self).__init__()
        css = """
        QTabBar{
        font-weight:bold;
        }
        """

        self.setStyleSheet(css)

        self.inputSpecs = input_specs.InputSpecs(DEBUG = False)
        self.inputSpecs.setObjectName("inputSpecs")
        self.inputFiles = input_files.InputFiles(DEBUG = False)
        self.inputFiles.setObjectName("inputFiles")
        self.inputCoeffs = input_coeffs.InputCoeffs(DEBUG = False)
        self.inputCoeffs.setObjectName("inputCoeffs")
        self.inputPZ = input_pz.InputPZ(DEBUG = False)
        self.inputPZ.setObjectName("inputPZ")
        self.inputInfo = input_info.InputInfo(DEBUG = False)
        self.inputInfo.setObjectName("inputInfo")        

        self.initUI()


    def initUI(self):
        """ Initialize UI with tabbed subplots """
        tabWidget = QtGui.QTabWidget()
        
        tabWidget.addTab(self.inputSpecs, 'Specs')
        tabWidget.addTab(self.inputFiles, 'Files')
        tabWidget.addTab(self.inputCoeffs, 'b,a')
        tabWidget.addTab(self.inputPZ, 'P/Z')
        tabWidget.addTab(self.inputInfo, 'Info')

        layVMain = QtGui.QVBoxLayout()
        layVMain.addWidget(tabWidget)
        
        #setContentsMargins -> number of pixels between frame window border
        layVMain.setContentsMargins(1,1,1,1) # R, T, L, B
#
        self.setLayout(layVMain)
        tabWidget.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Expanding)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # Collect "specs changed" / "filter designed" signals from all input 
        # widgets and route them to plot / input widgets that need to be updated
        #
        # sigSpecsChanged: signal indicating that filter SPECS have changed, 
        # requiring update of some plot widgets only:        
        self.inputSpecs.sigSpecsChanged.connect(self.updateSpecs)
        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        # requiring update of all plot and some input widgets:        
        self.inputSpecs.sigFilterDesigned.connect(self.updateAll)
        self.inputCoeffs.sigFilterDesigned.connect(self.updateAll)
        self.inputPZ.sigFilterDesigned.connect(self.updateAll)
        self.inputFiles.sigFilterDesigned.connect(self.updateAll)
        #----------------------------------------------------------------------


    def updateSpecs(self):
        """
        Called when filter SPECS have been changed:
        Update some input and plot widgets with new filter SPECS from global dict
        """
        self.inputSpecs.color_design_button("changed")      
        self.inputInfo.showInfo()
        self.sigSpecsChanged.emit() # pyFDA -> plot_all.updateSpecs
        

    def updateAll(self):
        """
        Called when a new filter has been DESIGNED
        - Update all input widgets that can / need to display new filter data,
            from the global filter dict.
        - Update all plot widgets via the signal sigFilterDesigned
        
        """
        if self.DEBUG: print("input_all.updateAll:\n",self.sender().objectName())

        self.inputSpecs.color_design_button("designed")      
        self.inputSpecs.loadAll()
        self.inputInfo.showInfo()
        self.inputCoeffs.showCoeffs()
        self.inputPZ.showZPK()

        self.sigFilterDesigned.emit() # pyFDA -> plot_all.updateAll


#------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = InputAll()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
    