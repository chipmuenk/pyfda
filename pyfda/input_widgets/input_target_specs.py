# -*- coding: utf-8 -*-
"""
Widget collecting subwidgets for the target filter specifications (currently
only amplitude and frequency specs.)

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import pyfda.filterbroker as fb
from pyfda.input_widgets import input_amp_specs, input_freq_specs


class InputTargetSpecs(QtGui.QWidget):
    """
    Build and update widget for entering the target specifications (frequencies
    and amplitudes) like F_sb, F_pb, A_SB, etc.
    """

    # class variables (shared between instances if more than one exists)
    sigSpecsChanged = pyqtSignal() # emitted when filter has been changed


    def __init__(self, parent, title = "Target Specs"):
        super(InputTargetSpecs, self).__init__(parent)

        self.title = title
        
        self._initUI()

#------------------------------------------------------------------------------
    def _initUI(self):
        """
        Initialize user interface
        """

        # subwidget for Frequency Specs
        self.f_specs = input_freq_specs.InputFreqSpecs(self, title = "Frequency")
        # subwidget for Amplitude Specs
        self.a_specs = input_amp_specs.InputAmpSpecs(self, title = "Amplitude")

        self.a_specs.setVisible(True)
        """
        LAYOUT
        """
        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        lblTitle = QtGui.QLabel(self) # field for widget title
        lblTitle.setText(self.title)
        lblTitle.setFont(bfont)
        
        layVFreq = QtGui.QVBoxLayout()  # add stretch at bottom of ampSpecs
        layVFreq.addWidget(self.f_specs) # to compensate for different number of 
        layVFreq.addStretch()           # arguments
        
        layVAmp = QtGui.QVBoxLayout()  # add stretch at bottom of freqSpecs
        layVAmp.addWidget(self.a_specs) # to compensate for different number of 
        layVAmp.addStretch()           # arguments
        
        layGMain = QtGui.QGridLayout()
        layGMain.addWidget(lblTitle,0,0,1,2)# title
        layGMain.addLayout(layVFreq,1,0)  # frequency specifications
        layGMain.addLayout(layVAmp,1,1)  # amplitude specifications

        layGMain.setContentsMargins(1,1,1,1)

        self.setLayout(layGMain)

        #----------------------------------------------------------------------
        #  SIGNALS & SLOTS
        self.a_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.f_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        
        self.update_UI() # first time initialization
        

#------------------------------------------------------------------------------
    def update_UI(self, freqParams = [], ampParams = []):
        """
        Pass frequency and amplitude labels to the amplitude and frequency
        spec widgets and emit a specs changed signal
        """

        # pass new labels to widgets
        # set widgets invisible if param list is empty
        self.f_specs.update_UI(new_labels = freqParams) # update frequency spec labels
        self.a_specs.setVisible(ampParams != [])
        self.a_specs.update_UI(new_labels = ampParams)

        self.sigSpecsChanged.emit() # ->pyFDA -> pltWidgets.updateAll()

#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Update entries from global dict fb.fil[0]
        parameters, using the "load_entries" methods of the classes
        """
        self.a_specs.load_entries() # magnitude specs with unit
        self.f_specs.load_entries() # weight specification

#------------------------------------------------------------------------------

if __name__ == '__main__':
    
    from PyQt4 import QtCore
    
    class MainWindow(QtGui.QMainWindow):
        """
        QMainWindow is used here as it is a class that understands GUI elements like
        toolbar, statusbar, central widget, docking areas etc.
        """

        def __init__(self):
            super(MainWindow, self).__init__()
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            self.main_widget = QtGui.QWidget()
            self.test_widget = InputTargetSpecs(self)           # instantiate widget

            layV = QtGui.QVBoxLayout(self.main_widget) # create layout manager
            layV.addWidget(self.test_widget)                 # add widget to layout
#            self.main_widget.setFocus()             # give keyboard focus to main_widget
            self.setCentralWidget(self.main_widget)
            # Set the given widget to be the main window's central widget, QMainWindow
            #  takes ownership of the widget pointer and deletes it at the appropriate time.

        def update_UI(self, freq_params, amp_params):
            self.test_widget.update_UI(freq_params, amp_params)
#------------------------------------------------------------------------------

    # Read freq / amp / weight labels for current filter design
    rt = fb.fil[0]['rt']
    ft = fb.fil[0]['ft']
    dm = fb.fil[0]['dm']

    if 'min' in fb.fil_tree[rt][ft][dm]:
        myParams = fb.fil_tree[rt][ft][dm]['min']['par']
    else:
        myParams = {}

    # build separate parameter lists according to the first letter
    freqParams = [l for l in myParams if l[0] == 'F']
    ampParams = [l for l in myParams if l[0] == 'A']
#-----------------------------------------------

    app = QtGui.QApplication(sys.argv) # instantiate app, pass command line arguments

    main_window = MainWindow()
    main_window.update_UI(freqParams, ampParams)


    app.setActiveWindow(main_window)
    # Sets the active window to the active widget in response to a system event.
    # The function is called from the platform specific event handlers.
    # It sets the activeWindow() and focusWidget() attributes and sends proper 
    # WindowActivate/WindowDeactivate and FocusIn/FocusOut events to all appropriate 
    # widgets. The window will then be painted in active state (e.g. cursors in 
    # line edits will blink), and it will have tool tips enabled.
    # Warning: This function does not set the keyboard focus to the active widget. 
    # Call QWidget.activateWindow() instead.

    main_window.show()

    ret = app.exec_()
    del main_window
    sys.exit(ret)


#------------------------------------------------------------------------------

#if __name__ == '__main__':
#    app = QtGui.QApplication(sys.argv)
#
#    # Read freq / amp / weight labels for current filter design
#    rt = fb.fil[0]['rt']
#    ft = fb.fil[0]['ft']
#    dm = fb.fil[0]['dm']
#
#    if 'min' in fb.fil_tree[rt][ft][dm]:
#        myParams = fb.fil_tree[rt][ft][dm]['min']['par']
#    else:
#        myParams = {}
#
#    # build separate parameter lists according to the first letter
#    freqParams = [l for l in myParams if l[0] == 'F']
#    ampParams = [l for l in myParams if l[0] == 'A']
#
#    form = InputTargetSpecs(title = "Test Specs")
#    form.update_UI(freqParams, ampParams)
#    form.show()
#
#    app.exec_()
