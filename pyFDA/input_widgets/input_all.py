# -*- coding: utf-8 -*-
"""
Created on Jan 5th

@author: Christian Muenker

Tabbed container for input widgets
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
    inputUpdated = pyqtSignal()  # emitted when input widget is updated


    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputAll, self).__init__()


#        self.inputParams = inputParams.inputParams()
        self.inputSpecs = input_specs.InputSpecs(DEBUG = False)
        self.inputFiles = input_files.InputFiles(DEBUG = False)
        self.inputCoeffs = input_coeffs.InputCoeffs(DEBUG = True)
        self.inputPZ = input_pz.InputPZ(DEBUG = True)
        self.inputInfo = input_info.InputInfo(DEBUG = False)

        self.initUI()


    def initUI(self):
        """ Initialize UI with tabbed subplots """
        tabWidget = QtGui.QTabWidget()
#        tab_widget.addTab(self.inputParams, 'Params')
        tabWidget.addTab(self.inputSpecs, 'Specs')
        tabWidget.addTab(self.inputFiles, 'Files')
        tabWidget.addTab(self.inputCoeffs, 'b,a')
        tabWidget.addTab(self.inputPZ, 'P/Z')
        tabWidget.addTab(self.inputInfo, 'Info')

        layVMain = QtGui.QVBoxLayout()
        layVMain.addWidget(tabWidget)
#
        self.setLayout(layVMain)
#        layVMain.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        tabWidget.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Expanding)

        # ============== Signals & Slots ================================

#        self.inputSpecs.fspecs.specsChanged.connect(self.updateAll)
#        self.inputSpecs.filterDesigned.connect(self.updateAll)
#        self.inputCoeffs.butUpdate.clicked.connect(self.updateAll)

        self.inputSpecs.filterChanged.connect(self.inputInfo.showInfo)



    def updateAll(self):
        """ Update all widgets with new filter data"""
        self.inputCoeffs.showCoeffs()
        self.inputPZ.showZPK()

#------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = InputAll()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()


