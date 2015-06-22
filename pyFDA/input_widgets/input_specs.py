# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 15:21:19 2013
Widget for entering filter specifications

@author: beike, Christian Münker
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

import filterbroker as fb
#from filter_tree_builder import FilterTreeBuilder

from input_widgets import (input_filter, input_order, input_amp_specs,
                           input_freq_specs, input_weight_specs, input_target_specs)


class InputSpecs(QtGui.QWidget):
    """
    Build widget for entering all filter specs
    """
    # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal() # emitted when specs have been changed

    def __init__(self, DEBUG = True):
        super(InputSpecs, self).__init__()
#        self.setStyleSheet("margin:5px; border:1px solid rgb(0, 0, 0); ")
#        self.setStyleSheet("background-color: rgb(255,0,0); margin:5px; border:1px solid rgb(0, 255, 0); ")


        self.DEBUG = DEBUG
#        self.ftb = FilterTreeBuilder('init.txt', 'filter_design',
#                                    commentChar = '#', DEBUG = DEBUG) #
        self.initUI()

    def initUI(self):
        """
        Create all widgets:

        selfil : Select Filter with response type rt (LP, ...),
              filter type ft (IIR, ...), and design method dm (cheby1, ...)
        filord : Filter Order (numeric or 'min')
        fspecs : Frequency Specifications
        ms : Magnitude Specifications with the subwidgets
            txt : only text field for comments / instruction
            val : infostring (title), Label, value
            unt : unit, label, value

        """

        self.selfil = input_filter.InputFilter(DEBUG = False)
        self.filord = input_order.InputOrder(DEBUG = False)
        # subwidget for Frequency Specs
        self.fspecs = input_freq_specs.InputFreqSpecs(DEBUG = False)
        self.fspecs.setObjectName("freqSpecs")
        # subwidget for Amplitude Specs
        self.aspecs = input_amp_specs.InputAmpSpecs(DEBUG = False)
        self.aspecs.setObjectName("ampSpecs")
        # subwidget for Weight Specs
        self.wspecs = input_weight_specs.InputWeightSpecs(DEBUG = False)
        self.wspecs.setObjectName("weightSpecs")

#TODO: get target specs up and running
        self.tspecs = input_target_specs.InputTargetSpecs(DEBUG = False)

        self.lblMsg = QtGui.QLabel(self)
        self.lblMsg.setWordWrap(True)
#        self.lblMsg.setFrameShape(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)

        layVMsg = QtGui.QVBoxLayout()
        layVMsg.addWidget(self.lblMsg)

        frmMsg = QtGui.QFrame()
        frmMsg.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        frmMsg.setLayout(layVMsg)
        frmMsg.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Minimum)

        self.lblMsg.setVisible(True)
        self.wspecs.setVisible(True)
        self.aspecs.setVisible(True)

        self.butDesignFilt = QtGui.QPushButton("DESIGN FILTER", self)
        self.color_design_button("changed")
        self.butReadFiltTree = QtGui.QPushButton("Read Filters", self)
        self.butReadFiltTree.setToolTip("Re-read filter design directory and build filter design tree.")

        """
        LAYOUT
        """
        spcV = QtGui.QSpacerItem(0,0, QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        layGMain = QtGui.QGridLayout()
        layGMain.addWidget(self.selfil,0,0,1,2)  # Design method (IIR - ellip, ...)
        layGMain.addWidget(self.filord,1,0,1,2)  # Filter order
        layGMain.addWidget(self.fspecs,2,0,1,2)  # Freq. specifications
        layGMain.addWidget(self.aspecs,3,0)   # Amplitude specs
        layGMain.addWidget(self.wspecs,3,1)   # Weight specs
        layGMain.addWidget(frmMsg,4,0,1,2)  # Text message
#TODO: get target specs up and running
        layGMain.addWidget(self.tspecs,5,0,1,2)   # Target specs
        layGMain.addWidget(self.butDesignFilt, 6,0)
        layGMain.addWidget(self.butReadFiltTree, 6,1)
        layGMain.addItem(spcV,7,0)
        layGMain.setContentsMargins(1,1,1,1)

        self.setLayout(layGMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        # Call updateUI every time filter (order) method is changed
        # updateUI emits sigFilterChanged when it's finished
        self.filord.sigSpecsChanged.connect(self.updateAllUIs)  
        self.selfil.sigSpecsChanged.connect(self.updateAllUIs)  
        
        self.fspecs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.aspecs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.wspecs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)

        self.butDesignFilt.clicked.connect(self.startDesignFilt)
        self.butReadFiltTree.clicked.connect(self.selfil.ftb.initFilters)
        #----------------------------------------------------------------------

        self.updateAllUIs() # first time initialization


#------------------------------------------------------------------------------
    def updateAllUIs(self):
        """
        This method is called every time filter design method or order 
        (min / man) is changed. At this time, the actual filter object
        instance has been created from design method and order 
        (e.g. 'cheby1', 'min') in input_filter.py. Its handle has been stored
        in fb.filobj.
        
        fb.fil[0] (currently selected filter) is read, then general information 
        for the selected filter type and order (min/man) is gathered from 
        the filter tree [fb.filTree], i.e. which parameters are needed, which
        widgets are visible and which message shall be displayed.
        
        Then, all subwidgets are recreated and finally the signal 
        'sigSpecsChanged' is emitted.
        """

        # Read freq / amp / weight labels for current filter design
        rt = fb.fil[0]['rt']
        ft = fb.fil[0]['ft']
        dm = fb.fil[0]['dm']
        fo = fb.fil[0]['fo']
        myParams = fb.filTree[rt][ft][dm][fo]['par'] # all parameters e.g. 'F_SB'
        myEnbWdg = fb.filTree[rt][ft][dm][fo]['enb'] # enabled widgets
        myMsg    = fb.filTree[rt][ft][dm][fo]['msg'] # message

        # build separate parameter lists according to the first letter
        self.freqParams = [l for l in myParams if l[0] == 'F']
        self.ampParams = [l for l in myParams if l[0] == 'A']
        self.weightParams = [l for l in myParams if l[0] == 'W']
        if self.DEBUG:
            print("=== InputParams.chooseDesignMethod ===")
            print("selFilter:", fb.fil[0])
            print('myLabels:', myParams)
            print('ampLabels:', self.ampParams)
            print('freqLabels:', self.freqParams)
            print('weightLabels:', self.weightParams)

        # pass new labels to widgets and recreate UI
        # set widgets invisible if param list is empty
        self.filord.loadEntries()
        
        self.fspecs.updateUI(newLabels = self.freqParams)
        
        self.aspecs.setVisible(self.ampParams != [])
        self.aspecs.setEnabled("aspecs" in myEnbWdg)
        self.aspecs.updateUI(newLabels = self.ampParams)
        
        self.wspecs.setVisible(self.weightParams != [])
        self.wspecs.setEnabled("wspecs" in myEnbWdg)
        self.wspecs.updateUI(newLabels = self.weightParams)
#TODO: get target specs up and running
#        self.tspecs.updateUI(newLabels = (self.freqParams, self.ampParams))
        self.tspecs.setVisible(False)        
        self.lblMsg.setText(myMsg)

        self.sigSpecsChanged.emit()
        

#------------------------------------------------------------------------------        
    def storeAll(self):
        """
        Store currently selected filter in global dict fb.fil[0]
        parameters, using the "store" methods of the classes
        """
        # collect data from widgets and write to fb.fil[0]
        self.filord.storeEntries()   # filter order widget
        self.fspecs.storeEntries() # frequency specification widget
        self.aspecs.storeEntries() # magnitude specs with unit
        self.wspecs.storeEntries() # weight specification
#TODO: get target specs up and running
#        self.tspecs.storeEntries() # target specs        

#------------------------------------------------------------------------------
    def loadAll(self):
        """
        Update entries from global dict fb.fil[0]
        parameters, using the "load" methods of the classes
        """
        self.selfil.loadEntries() # select filter widget
        self.filord.loadEntries() # filter order widget
        self.fspecs.loadEntries() # frequency specification widget
        self.aspecs.loadEntries() # magnitude specs with unit
        self.wspecs.loadEntries() # weight specification
#TODO: get target specs up and running
        self.tspecs.loadEntries() # target specs

        if self.DEBUG: 
            print("=== pyFDA.py : storeAll ===")
            print(fb.fil[0])


#------------------------------------------------------------------------------
    def startDesignFilt(self):
        """
        Start the actual filter design process:
        - store the entries of all input widgets in the global filter dict.
        - call the design method, passing the whole dictionary as the
          argument: let the design method pick the needed specs
        - update the input widgets in case weights, corner frequencies etc.
          have been changed by the filter design method
        - the plots are updated via signal-slot connection
        """
#        self.storeAll() # store entries of all input widgets -> fb.fil[0]
#       this is not needed as individual subwidgets store results automatically
        if self.DEBUG:
            print("--- pyFDA.py : startDesignFilter: Specs ---")
            print('Specs:', fb.fil[0])#params)
            print("fb.fil[0]['dm']", fb.fil[0]['dm']+"."+
                  fb.fil[0]['rt']+fb.fil[0]['fo'])

        # Now construct the instance method from the response type (e.g.
        # 'LP'+'man' -> cheby1.LPman) and
        # design the filter by passing current specs to the method, yielding
        # e.g. cheby1.LPman(fb.fil[0])

        try:
            getattr(fb.filObj, fb.fil[0]['rt'] +
                                fb.fil[0]['fo'])(fb.fil[0])

            # The filter design routines write coeffs, poles/zeros etc. back to
            # the global filter dict
    
            # Update filter order. weights and freqs in case they have been changed
            self.filord.loadEntries()
            self.wspecs.loadEntries()
            self.fspecs.loadEntries()
            
            self.sigFilterDesigned.emit() # emit signal -> input_all
                                
        except Exception as e:
            print(e)
            print(e.__doc__)
            self.color_design_button("error")
            

        if self.DEBUG:
            print("=== pyFDA.py : startDesignFilter: Results ===")
            print("zpk:" , fb.fil[0]['zpk'])
            print('ndim coeffs:', np.ndim(fb.fil[0]['ba']))
            print("b,a = ", fb.fil[0]['ba'])
            print("N = ",fb.fil[0]['N'])
            print("F_PB, F_SB = ",fb.fil[0]['F_PB'], fb.fil[0]['F_SB'])
            
    def color_design_button(self, state):
        """
        Color the >> DESIGN FILTER << button:
        green:  filter has been designed, everything ok
        yellow: filter specs have been changed
        red:    an error has occurred during filter desigtn
        """
        if state == "designed": 
            css = "QPushButton { background-color: green;  color: white}"
        elif state == "changed": 
            css = "QPushButton { background-color: yellow}"
        elif state == "error": 
            css = "QPushButton { background-color: red; color: white}" #
        else: css = ""
        
        self.butDesignFilt.setStyleSheet(css +
                      "QPushButton:pressed { background-color: orange }" )

#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = InputSpecs()
    form.show()
    form.storeAll()

    app.exec_()







