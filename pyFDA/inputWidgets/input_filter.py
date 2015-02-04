# -*- coding: utf-8 -*-
"""
input_filter.py
---------------
Subwidget for selecting the filter, consisting of combo boxes for:
- Response Type (LP, HP, Hilbert, ...)
- Filter Type (IIR, FIR, CIC ...) 
- DesignMethod (Butterworth, ...)

@author: Julia Beike, Christian Münker
Datum: 4.12.2014
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb

class SelectFilter(QtGui.QWidget):
    """
    Construct combo boxes for selecting the filter, consisting of:
      - Response Type (LP, HP, Hilbert, ...)
      - Filter Type (IIR, FIR, CIC ...) 
      - DesignMethod (Butterworth, ...)
    """
    
    def __init__(self, DEBUG = True):
        super(SelectFilter, self).__init__()
        self.DEBUG = DEBUG
        self.initUI()
        
        self.setResponseType()
        
        
    def initUI(self): 
        """
        Initialize UI with comboboxes for selecting filter
        """
#-----------------------------------------------------------------------------
#        see filterBroker.py for structure and content of "filterTree" dict
#-----------------------------------------------------------------------------

        #----------------------------------------------------------------------
        # Create combo boxes 
        # - comboResponseType for selecting response type rt (LP, HP, ...)
		# - comboFilterType for selection of filter type (IIR, FIR, ...)
		# - comboDesignMethod for selection of design method (Chebychev, ...)
		# and populate them from the "filterTree" dict either directly or by
		# calling setResponseType() :
        self.comboResponseType=QtGui.QComboBox(self)
        self.comboResponseType.setToolTip("Select filter response type.")
        self.comboFilterType=QtGui.QComboBox(self)
        self.comboFilterType.setToolTip("Select the kind of filter (recursive, transversal, ...).")
        self.comboDesignMethod=QtGui.QComboBox(self)
        self.comboFilterType.setToolTip("Select the actual filter design method.")        
        
        # Translate short response type ("LP") to displayed names ("Lowpass")
        # (correspondence is defined in filterbroker.py) and populate combo box:
        for rt in fb.gD['filterTree']:
            self.comboResponseType.addItem(fb.gD['rtNames'][rt], rt)
        self.comboResponseType.setCurrentIndex(0) # set initial index



        """
        LAYOUT      
        """
        # see Summerfield p. 278       
        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(self.comboResponseType)# QtCore.Qt.AlignLeft)
        hLayout.addWidget(self.comboFilterType)
        hLayout.addWidget(self.comboDesignMethod)
        
        self.vLayout = QtGui.QVBoxLayout(self) 
        self.vLayout.addLayout(hLayout)
        
        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.vLayout)
        
        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(sfFrame)
        self.setLayout(mainLayout)
#        mainLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        #------------------------------------------------------------
        # SIGNALS & SLOTS      
        #
        # Connect comboBoxes and setters
        
        self.comboResponseType.activated.connect(self.setResponseType) # 'LP'
        self.comboFilterType.activated.connect(self.setFilterType) #'IIR'
        self.comboDesignMethod.activated.connect(self.setDesignMethod) #'cheby1'

    def updateLayout(self):
        """
        Dynamically add and remove subwidgets as needed
        """
        #if ... :
        print(fb.gD['selFilter']['inst'])
        self.xxx = QtGui.QComboBox(self)
        self.vLayout.addWidget(self.xxx)
        
        
        self.vLayout.removeWidget(self.xxx)
        self.xxx.deleteLater()
        del self.xxx

    def setResponseType(self):
        """
        Triggered when comboResponseType (LP, HP, ...) is changed:
        Copy selection to self.rt and fb.gD and reconstruct filter type combo
        """ 
        self.rtIdx =self.comboResponseType.currentIndex()       
        self.rt = str(self.comboResponseType.itemData(self.rtIdx))
         
        fb.gD['selFilter']['rt'] = self.rt # abbreviation
#        rt=fb.gD["rtNames"][self.rt] # full text
#        print(fb.gD['filterTree'][self.rt].keys())
        # 
        self.comboFilterType.clear() 
        self.comboFilterType.addItems(
            fb.gD['filterTree'][self.rt].keys())
        self.setFilterType()
        
    def setFilterType(self):
        """"
        Triggered when comboFilterType (IIR, FIR, ...) is changed: 
        Copy selected setting to self.ft and (re)construct design method combo, 
        adding displayed text (e.g. "Chebychev 1") and hidden data (e.g. "cheby1")
        """
        self.ft = str(self.comboFilterType.currentText())
        self.comboDesignMethod.clear()  

        for dm in fb.gD['filterTree'][self.rt][self.ft]:
            self.comboDesignMethod.addItem(fb.gD['dmNames'][dm], dm)

        fb.gD['selFilter']['ft'] = self.ft
        self.setDesignMethod()
            
    def setDesignMethod(self):
        """
        Triggered when comboDesignMethod (cheby1, ...) is changed: 
        Copy selected setting to self.dm # TODO: really needed? 
        """
        self.dmIdx = self.comboDesignMethod.currentIndex()
        self.dm = str(self.comboDesignMethod.itemData(self.dmIdx))
        fb.gD['selFilter']['dm'] = self.dm

        # Check whether new design method also provides the old filter order 
        # method. If yes, don't change it, else set first available 
        # filter method
        if fb.gD['selFilter']['fo'] not in \
                        fb.gD['filterTree'][self.rt][self.ft][self.dm].keys():
            fb.gD['selFilter'].update({'fo':{}})
            fb.gD['selFilter']['fo'] \
                = fb.gD['filterTree'][self.rt][self.ft][self.dm].keys()[0]
        if self.DEBUG:
            print("=== InputFilter.setDesignMethod ===")
            print("selFilter:", fb.gD['selFilter'])
            print("filterTree[dm] = ", fb.gD['filterTree'][self.rt][self.ft]\
                                                            [self.dm])
            print("filterTree[dm].keys() = ", fb.gD['filterTree'][self.rt][self.ft]\
                                                            [self.dm].keys())
                                                            
                
        self.updateLayout() # check for new subwidgets and update if needed

        # reverse dictionary lookup
        #key = [key for key,value in dict.items() if value=='value' ][0]        

#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = SelectFilter(DEBUG = True)
    form.show()
   
    app.exec_()

