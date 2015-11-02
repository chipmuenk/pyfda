# -*- coding: utf-8 -*-
"""
Widget collecting subwidgets for the target filter specifications (currently
only amplitude and frequency specs.)

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import numpy as np
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


    def __init__(self, DEBUG = False, title = "Target Specs"):
        super(InputTargetSpecs, self).__init__()


        self.DEBUG = DEBUG
        self.title = title
        
        self._initUI()


#------------------------------------------------------------------------------
    def _initUI(self):
        """
        Initialize user interface
        """

        # subwidget for Frequency Specs
        self.fspecs = input_freq_specs.InputFreqSpecs(DEBUG = False, 
                                                      title = "Frequency")
        # subwidget for Amplitude Specs
        self.aspecs = input_amp_specs.InputAmpSpecs(DEBUG = False, 
                                                    title = "Amplitude")

        self.aspecs.setVisible(True)
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
        layVFreq.addWidget(self.fspecs) # to compensate for different number of 
        layVFreq.addStretch()           # arguments
        
        layVAmp = QtGui.QVBoxLayout()  # add stretch at bottom of freqSpecs
        layVAmp.addWidget(self.aspecs) # to compensate for different number of 
        layVAmp.addStretch()           # arguments
        
        layGMain = QtGui.QGridLayout()
        layGMain.addWidget(lblTitle,0,0,1,2)# title
        layGMain.addLayout(layVFreq,1,0)  # frequency specifications
        layGMain.addLayout(layVAmp,1,1)  # amplitude specifications

        layGMain.setContentsMargins(1,1,1,1)

        self.setLayout(layGMain)

        #----------------------------------------------------------------------
        #  SIGNALS & SLOTS
        self.aspecs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.fspecs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        
        self.update_UI() # first time initialization
        

#------------------------------------------------------------------------------
    def update_UI(self, freqParams = [], ampParams = []):
        """
        Pass frequency and amplitude labels to the amplitude and frequency
        spec widgets and emit a specs changed signal
        """

        # pass new labels to widgets
        # set widgets invisible if param list is empty
        self.fspecs.update_UI(newLabels = freqParams) # update frequency spec labels
        self.aspecs.setVisible(ampParams != [])
        self.aspecs.update_UI(newLabels = ampParams)

        self.sigSpecsChanged.emit() # ->pyFDA -> pltWidgets.updateAll()

#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Update entries from global dict fb.fil[0]
        parameters, using the "load_entries" methods of the classes
        """
        self.aspecs.load_entries() # magnitude specs with unit
        self.fspecs.load_entries() # weight specification

#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

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

    form = InputTargetSpecs(title = "Test Specs")
    form.update_UI(freqParams, ampParams)
    form.show()

    app.exec_()







