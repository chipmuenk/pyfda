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

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

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
        
        self.initUI()


#------------------------------------------------------------------------------
    def initUI(self):
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
        # NO   SIGNALS & SLOTS

        self.updateUI() # first time initialization
        

#------------------------------------------------------------------------------
    def updateUI(self, freqParams = [], ampParams = []):
        """
        Pass frequency and amplitude labels to the amplitude and frequency
        spec widgets and emit a specs changed signal
        """

        # pass new labels to widgets
        # set widgets invisible if param list is empty
        self.fspecs.updateUI(newLabels = freqParams) # update frequency spec labels
        self.aspecs.setVisible(ampParams != [])
        self.aspecs.updateUI(newLabels = ampParams)

        self.sigSpecsChanged.emit() # ->pyFDA -> pltWidgets.updateAll()

#------------------------------------------------------------------------------
    def storeEntries(self):
        """
        Update global dict fb.fil[0] with currently selected filter
        parameters, using the update methods of the classes
        """
        # collect data from widgets and write to fb.fil[0]
        self.fspecs.storeEntries() # frequency specification widget
        self.aspecs.storeEntries() # magnitude specs with unit

        if self.DEBUG: print(fb.fil[0])

#------------------------------------------------------------------------------
    def loadEntries(self):
        """
        Update entries from global dict fb.fil[0]
        parameters, using the "load" methods of the classes
        """
        self.aspecs.loadEntries() # magnitude specs with unit
        self.fspecs.loadEntries() # weight specification


#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    # Read freq / amp / weight labels for current filter design
    rt = fb.fil[0]['rt']
    ft = fb.fil[0]['ft']
    dm = fb.fil[0]['dm']
#        fo = fb.fil[0]['fo']
#        print(fb.filTree[rt][ft])
    if 'min' in fb.filTree[rt][ft][dm]:
        myParams = fb.filTree[rt][ft][dm]['min']['par']
    else:
        myParams = {}
#        myEnbWdg = fb.filTree[rt][ft][dm][fo]['enb'] # enabled widgets

    # build separate parameter lists according to the first letter
    freqParams = [l for l in myParams if l[0] == 'F']
    ampParams = [l for l in myParams if l[0] == 'A']

    form = InputTargetSpecs(title = "Test Specs")
    form.updateUI(freqParams, ampParams)
    form.show()
    form.storeEntries()

    app.exec_()







