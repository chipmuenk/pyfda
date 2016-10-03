# -*- coding: utf-8 -*-
"""
Tabbed container with all input widgets

Author: Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal
#import pyfda.filterbroker as fb

from pyfda.input_widgets import input_specs_test as input_specs#, input_pz#, input_info

#from pyfda.input_widgets import input_specs#, input_pz#, input_info


class InputTabWidgets(QtGui.QWidget):
    """
    Create a tabbed widget for various input subwidgets
    """
    # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal()  # emitted when specs have been changed


    def __init__(self, parent):
        super(InputTabWidgets, self).__init__(parent)

        self.inputSpecs = input_specs.InputSpecs(self)
        self.inputSpecs.setObjectName("inputSpecs")


#        self.inputFiles = input_files.InputFiles(self)
 #       self.inputFiles.setObjectName("inputFiles")

#        self.inputCoeffs = input_coeffs.InputCoeffs(self)
#        self.inputCoeffs.setObjectName("inputCoeffs")

#        self.inputPZ = input_pz.InputPZ(self)
#        self.inputPZ.setObjectName("inputPZ")

        self._init_UI()


    def _init_UI(self):
        """ Initialize UI with tabbed input widgets """
        tabWidget = QtGui.QTabWidget()
        tabWidget.setObjectName("TabWidg")

        tabWidget.addTab(self.inputSpecs, 'Specs')
#        tabWidget.addTab(self.inputFiles, 'Files')
#        tabWidget.addTab(self.inputCoeffs, 'b,a')
#        tabWidget.addTab(self.inputPZ, 'P/Z')


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
        # Check:
        #http://www.pythoncentral.io/pysidepyqt-tutorial-creating-your-own-signals-and-slots/#custom-tab-2-pyqt
        #
        # sigSpecsChanged: signal indicating that filter SPECS have changed, 
        #       requiring update of some plot widgets and input widgets:        
#        self.inputCoeffs.sigFilterDesigned.connect(self.update_all)
#        self.inputPZ.sigFilterDesigned.connect(self.update_all)
        
#        self.inputFiles.sigFilterLoaded.connect(self.load_all)

        #----------------------------------------------------------------------

    def update_view(self):
        """
        Slot for InputSpecs.sigViewChanged
        
        Propagate new PLOT VIEW (e.g. log scale) to plot widgets via pyfda.py
            
        Update plot widgets via sigSpecsChanged signal that need new
            specs, e.g. plotHf widget for the filter regions
        """

#        self.inputInfo.load_entries() # could update log. / lin. units (not implemented)
        self.sigSpecsChanged.emit() # pyFDA -> PlotTabWidgets.update_specs


    def update_specs(self):
        """
        Slot for InputSpecs.sigSpecsChanged
        
        Propagate new filter SPECS from filter dict to other input widgets and 
        to plot widgets via pyfda.py
            
        - Update input widgets that can / need to display specs (except inputSpecs
             - the origin of the signal !!)
        - Update plot widgets via sigSpecsChanged signal that need new
            specs, e.g. plotHf widget for the filter regions
        """
        pass
        
    def load_all(self):
        """
        Called when a new filter has been LOADED: 
        Pass new filter data from the global filter dict
        - Specifically call InputFilter.load_entries
        - Update the input widgets that can / need to display filter data
        - Update all plot widgets via the signal sigFilterDesigned
        """
        self.update_all()


    def update_all(self):
        """
        Slot for sigFilterDesigned from InputSpecs, InputCoeffs, InputPZ      
        
        Called when a new filter has been DESIGNED: 
            Pass new filter data from the global filter dict
        - Update the input widgets that can / need to display filter data
        - Update all plot widgets via the signal sigFilterDesigned
        
        """
#        self.inputCoeffs.load_entries()
#        self.inputPZ.load_entries()


        self.sigFilterDesigned.emit() # pyFDA -> PlotTabWidgets.update_data


#------------------------------------------------------------------------

def main():
    from pyfda import pyfda_rc as rc
    app = QtGui.QApplication(sys.argv)
    app.setStyleSheet(rc.css_rc)

    mainw = InputTabWidgets(None)
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    