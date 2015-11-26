# -*- coding: utf-8 -*-
"""
Tabbed container with all input widgets

Author: Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import logging
logger = logging.getLogger(__name__)
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, pyqtSlot

try:
    import myhdl
except ImportError:
    MYHDL = False
else:
    MYHDL = True
    logger.info("Info: Module myHDL found -> filter synthesis enabled!")

from pyfda.input_widgets import input_specs, input_files, input_coeffs, input_info, input_pz
if MYHDL:
    from pyfda.hdl_generation import hdl_specs


class InputTabWidgets(QtGui.QWidget):
    """
    Create a tabbed widget for various input subwidgets
    """
    # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal()  # emitted when specs have been changed


    def __init__(self):
        super(InputTabWidgets, self).__init__()
        css = """
        QTabBar{
        font-weight:bold;
        }
        """

        self.setStyleSheet(css)

        self.inputSpecs = input_specs.InputSpecs(DEBUG = False)
        self.inputSpecs.setObjectName("inputSpecs")
        self.inputFiles = input_files.InputFiles()
        self.inputFiles.setObjectName("inputFiles")
        self.inputCoeffs = input_coeffs.InputCoeffs(DEBUG = False)
        self.inputCoeffs.setObjectName("inputCoeffs")
        self.inputPZ = input_pz.InputPZ(DEBUG = False)
        self.inputPZ.setObjectName("inputPZ")
        self.inputInfo = input_info.InputInfo(DEBUG = False)
        self.inputInfo.setObjectName("inputInfo")
        if MYHDL:
            self.hdlSpecs = hdl_specs.HDLSpecs()

        self.initUI()


    def initUI(self):
        """ Initialize UI with tabbed input widgets """
        tabWidget = QtGui.QTabWidget()
        tabWidget.setObjectName("TabWidg")
#        tabWidget.setStyleSheet(user_settings.css_rc['QTabBar'])
#        tabWidget.setTabShape(QtGui.QTabWidget.Triangular) # different look ....
        tabWidget.addTab(self.inputSpecs, 'Specs')
        tabWidget.addTab(self.inputFiles, 'Files')
        tabWidget.addTab(self.inputCoeffs, 'b,a')
        tabWidget.addTab(self.inputPZ, 'P/Z')
        tabWidget.addTab(self.inputInfo, 'Info')
        if MYHDL:
            tabWidget.addTab(self.hdlSpecs, 'HDL')
#        QTabBar.setTabTextColor() 
#        css = "QTabWidget { background-color: red; color: white}" 
#        self.inputInfo.setStyleSheet(css)#

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
        #       requiring update of some plot widgets only:        
        self.inputSpecs.sigSpecsChanged.connect(self.updateSpecs)
# TODO: connect to a specific slot
        self.inputSpecs.sigViewChanged.connect(self.updateSpecs)
        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        #       requiring update of all plot and some input widgets:        
        self.inputSpecs.sigFilterDesigned.connect(self.updateAll)
        self.inputCoeffs.sigFilterDesigned.connect(self.updateAll)
        self.inputPZ.sigFilterDesigned.connect(self.updateAll)
        
        self.inputFiles.sigFilterLoaded.connect(self.loadAll)
        #----------------------------------------------------------------------


    def updateSpecs(self):
        """
        Slot for InputSpecs.sigSpecsChanged and InputSpecs.sigViewChanged
        
        Propagate new filter SPECS from filter dict to other input widgets and 
        to plot widgets via pyfda.py
            
        - Update input widgets that can / need to display specs (except inputSpecs
             - the origin of the signal !!)
        - Update plot widgets via sigSpecsChanged signal that need new
            specs, e.g. plotHf widget for the filter regions
        """
# TODO: The button should be styled within InputSpecs
        self.inputSpecs.color_design_button("changed")
        self.inputInfo.showInfo()
        self.sigSpecsChanged.emit() # pyFDA -> plot_widgets.updateSpecs
        
    def loadAll(self):
        """
        Called when a new filter has been LOADED: 
        Pass new filter data from the global filter dict
        - Specifically call InputFilter.load_all_specs
        - Update the input widgets that can / need to display filter data
        - Update all plot widgets via the signal sigFilterDesigned
        """
        self.inputSpecs.sel_fil.load_entries() # update input_filters
        self.updateAll()


    def updateAll(self):
        """
        Slot for sigFilterDesigned from InputSpecs, InputCoeffs, InputPZ      
        
        Called when a new filter has been DESIGNED: 
            Pass new filter data from the global filter dict
        - Update the input widgets that can / need to display filter data
        - Update all plot widgets via the signal sigFilterDesigned
        
        """
        logger.info("input_widgets.updateAll:\n",self.sender().objectName())

        self.inputSpecs.color_design_button("ok")  
# TODO: The following should be handled within InputSpecs ?
        self.inputSpecs.load_all_specs()
        self.inputInfo.showInfo()
        self.inputCoeffs.load_entries()
        self.inputPZ.showZPK()

        self.sigFilterDesigned.emit() # pyFDA -> plot_all.updateAll


#------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = InputTabWidgets()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
    