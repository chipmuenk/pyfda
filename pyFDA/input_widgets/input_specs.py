# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 15:21:19 2013
Widget for entering filter specifications

@author: beike, Christian Münker
"""
from __future__ import print_function, division, unicode_literals
import sys, os 
import numpy as np
from PyQt4 import QtGui

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb
#from filter_tree_builder import FilterTreeBuilder
    
import input_filter, input_order, input_amp_specs, input_freq_specs,\
    input_weight_specs
from plot_widgets import plot_all


class InputSpecs(QtGui.QWidget):
    """
    Build widget for entering all filter specs
    """
    
    def __init__(self, DEBUG = False):
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

        sf : Select Filter with response type rt (LP, ...), 
              filter type ft (IIR, ...), and design method dm (cheby1, ...)
        fo : Filter Order (numeric or 'min')
        fspec : Frequency Specifications 
        ms : Magnitude Specifications with the subwidgets
            txt : only text field for comments / instruction
            val : infostring (title), Label, value
            unt : unit, label, value

        """ 

        self.sf = input_filter.SelectFilter(DEBUG = True)
        self.fo = input_order.InputOrder(DEBUG = False)
        # subwidget for Frequency Specs
        self.fspec = input_freq_specs.InputFreqSpecs(specs = fb.fil[0],
                    DEBUG = False)
        # subwidget for Amplitude Specs        
        self.aspec = input_amp_specs.InputAmpSpecs(specs = fb.fil[0],
                    DEBUG = False)
        # subwidget for Weight Specs                                           
        self.wspec = input_weight_specs.InputWeightSpecs(specs = fb.fil[0],
                    DEBUG = False)
        
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
        self.wspec.setVisible(True)
        self.aspec.setVisible(True)
        
        self.butDesignFilt = QtGui.QPushButton("DESIGN FILTER", self)
        self.butReadFiltTree = QtGui.QPushButton("Read Filters", self)
        self.butReadFiltTree.setToolTip("Re-read filter design directory and build filter design tree.")

        """
        LAYOUT      
        """
        spcV = QtGui.QSpacerItem(0,0, QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        layGMain = QtGui.QGridLayout()
        layGMain.addWidget(self.sf,0,0,1,2)  # Design method (IIR - ellip, ...)
        layGMain.addWidget(self.fo,1,0,1,2)  # Filter order
        layGMain.addWidget(self.fspec,2,0,1,2)  # Freq. specifications
        layGMain.addWidget(self.aspec,3,0)   # Amplitude specs
        layGMain.addWidget(self.wspec,3,1)   # Weight specs
        layGMain.addWidget(frmMsg,4,0,1,2)  # Text message
        layGMain.addItem(spcV,5,0)
        layGMain.addWidget(self.butDesignFilt, 6,0)
        layGMain.addWidget(self.butReadFiltTree, 6,1)

        self.setLayout(layGMain)
        
        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        # Call chooseDesignMethod every time filter selection is changed: 
        self.fo.chkMin.clicked.connect(self.chooseDesignMethod)
        self.sf.cmbResponseType.activated.connect(self.chooseDesignMethod)
        self.sf.cmbFilterType.activated.connect(self.chooseDesignMethod)
        self.sf.cmbDesignMethod.activated.connect(self.chooseDesignMethod)
        self.fo.chkMin.clicked.connect(self.chooseDesignMethod)
        self.butDesignFilt.clicked.connect(self.startDesignFilt)
        self.butReadFiltTree.clicked.connect(self.sf.ftb.initFilters)

        self.chooseDesignMethod() # first time initialization
        
    def chooseDesignMethod(self):
        """
        Reads:  fb.fil[0] (currently selected filter), extracting info
                from fb.filTree
        Writes:
        Depending on SelectFilter and frequency specs, the values of the 
        widgets fo, fspec are recreated. For widget ms, the visibility is changed
        as well.
        """
        
        # filter object instance is created from design method 
        # (e.g. 'cheby1', 'min') in input_filter.py  

        # Read freq / amp / weight labels for current filter design
        rt = fb.fil[0]['rt']
        ft = fb.fil[0]['ft']
        dm = fb.fil[0]['dm']
        fo = fb.fil[0]['fo']  
        myParams = fb.filTree[rt][ft][dm][fo]['par']
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

        # pass new labels to widgets
        # set widgets invisible if param list is empty
        self.fo.updateEntries()
        self.fspec.setEntries(newLabels = self.freqParams) # update frequency spec labels
        self.aspec.setVisible(self.ampParams != [])
        self.aspec.setEnabled("aspec" in myEnbWdg)
        self.aspec.setEntries(newLabels = self.ampParams)
        self.wspec.setVisible(self.weightParams != []) 
        self.wspec.setEnabled("wspec" in myEnbWdg)
        self.wspec.setEntries(newLabels = self.weightParams)
        self.lblMsg.setText(myMsg)
            
    def storeAll(self):
        """
        Update global dict fb.fil[0] with currently selected filter 
        parameters, using the update methods of the classes
        """
        # collect data from widgets and write to fb.fil[0]
        self.fo.updateEntries()   # filter order widget
        self.fspec.storeEntries() # frequency specification widget
        self.aspec.storeEntries() # magnitude specs with unit
        self.wspec.storeEntries() # weight specification  
            
        if self.DEBUG: print(fb.fil[0])
  
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
        self.storeAll() # store entries of all input widgets -> fb.fil[0] 
        if self.DEBUG:
            print("--- pyFDA.py : startDesignFilter ---")
            print('Specs:', fb.fil[0])#params)
            print("fb.fil[0]['dm']", fb.fil[0]['dm']+"."+
                  fb.fil[0]['rt']+fb.fil[0]['fo'])

        # Now construct the instance method from the response type (e.g.
        # 'LP'+'man' -> cheby1.LPman) and
        # design the filter by passing current specs to the method, yielding 
        # e.g. cheby1.LPman(fb.fil[0])
        getattr(fb.filObj, fb.fil[0]['rt'] +
                                fb.fil[0]['fo'])(fb.fil[0])
        # The filter design routines write coeffs, poles/zeros etc. back to 
        # the global filter dict
                                
        # Update filter order. weights and freqs in case they have been changed
        self.fo.updateEntries()
        self.wspec.loadEntries()
        self.fspec.loadEntries()
        
        if self.DEBUG:
            print("=== pyFDA.py : startDesignFilter ===")
            print("zpk:" , fb.fil[0]['zpk'])
            print('ndim gD:', np.ndim(fb.fil[0]['coeffs']))
            print("b,a = ", fb.fil[0]['coeffs'])
            print("N = ",fb.fil[0]['N'])
        print("F_PB, F_SB = ",fb.fil[0]['F_PB'], fb.fil[0]['F_SB'])
     
#        self.pltAll.update() is executed from pyFDA.py via signal-slot conn.!
  
#------------------------------------------------------------------------------ 
   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = InputSpecs()
    form.show()
    form.storeAll()
   
    app.exec_()


   
        



 