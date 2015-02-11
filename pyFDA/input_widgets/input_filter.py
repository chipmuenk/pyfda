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

# TODO: Add subwidgets, depending on filterSel parameters

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb
from filter_tree_builder import FilterTreeBuilder

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
        self.ftb = FilterTreeBuilder('init.txt', 'filter_design', 
                                    commentChar = '#', DEBUG = DEBUG) #                                             
        
        
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
        self.hLayout2 = QtGui.QHBoxLayout() # for additional subwidgets
        self.dynWdgFrame = QtGui.QFrame() # collect subwidgets in frame (no border)
        self.dynWdgFrame.setLayout(self.hLayout2)
        
        hLayout = QtGui.QHBoxLayout() # container for standard subwidgets
        hLayout.addWidget(self.comboResponseType)# QtCore.Qt.AlignLeft)
        hLayout.addWidget(self.comboFilterType)
        hLayout.addWidget(self.comboDesignMethod)

        # stack standard + dynamic subwidgets vertically:       
        vLayout = QtGui.QVBoxLayout()
        vLayout.addLayout(hLayout)
        vLayout.addWidget(self.dynWdgFrame)
        
        self.sfFrame = QtGui.QFrame()
        self.sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.sfFrame.setLayout(vLayout)
        
        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(self.sfFrame)
        self.setLayout(mainLayout)
#        mainLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        #------------------------------------------------------------
        # SIGNALS & SLOTS      
        #
        # Connect comboBoxes and setters
        
        self.comboResponseType.activated.connect(self.setResponseType) # 'LP'
        self.comboFilterType.activated.connect(self.setFilterType) #'IIR'
        self.comboDesignMethod.activated.connect(self.setDesignMethod) #'cheby1'


    def setResponseType(self):
        """
        Triggered when comboResponseType (LP, HP, ...) is changed:
        Copy selection to self.rt and fb.gD and reconstruct filter type combo
        """ 
        self.rtIdx =self.comboResponseType.currentIndex()       
        self.rt = str(self.comboResponseType.itemData(self.rtIdx))
         
        fb.fil[0]['rt'] = self.rt # abbreviation
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

        fb.fil[0]['ft'] = self.ft
        self.setDesignMethod()
            
    def setDesignMethod(self):
        """
        Triggered when comboDesignMethod (cheby1, ...) is changed: 
        Copy selected setting to self.dm # TODO: really needed? 
        """
        self.dmIdx = self.comboDesignMethod.currentIndex()
        self.dm = str(self.comboDesignMethod.itemData(self.dmIdx))
        fb.fil[0]['dm'] = self.dm
        
        try: # has a filter object been instantiated yet?
            if fb.fil[0]['dm'] not in fb.filObj.name:
                fb.filObj = self.ftb.objectWizzard(fb.fil[0]['dm'])
        except AttributeError as e: # No, create a filter instance
            print (e)
            fb.filObj = self.ftb.objectWizzard(fb.fil[0]['dm'])

        # Check whether new design method also provides the old filter order 
        # method. If yes, don't change it, else set first available 
        # filter order method
        if fb.fil[0]['fo'] not in \
                        fb.gD['filterTree'][self.rt][self.ft][self.dm].keys():
            fb.fil[0].update({'fo':{}})
            fb.fil[0]['fo'] \
                = fb.gD['filterTree'][self.rt][self.ft][self.dm].keys()[0]

        if self.DEBUG:
            print("=== InputFilter.setDesignMethod ===")
            print("selFilter:", fb.fil[0])
            print("filterTree[dm] = ", fb.gD['filterTree'][self.rt][self.ft]\
                                                            [self.dm])
            print("filterTree[dm].keys() = ", fb.gD['filterTree'][self.rt][self.ft]\
                                                            [self.dm].keys())
                                                            
                
        self.updateWidgets() # check for new subwidgets and update if needed

        # reverse dictionary lookup
        #key = [key for key,value in dict.items() if value=='value' ][0]        
    def updateWidgets(self):
        """
        Delete dynamically created subwidgets and create new ones, depending
        on requirements of filter design algorithm
        """
        self._delWidgets()
        try:              
            if 'sf' in fb.filObj.wdg:
                a = getattr(fb.filObj, fb.filObj.wdg['sf'])
                self.hLayout2.addWidget(a)
                self.hLayout2.addStretch()
                self.dynWdgFrame.setVisible(a != None)

        except AttributeError as e:
            print("sf.updateWidgets:",e)
            self.dynWdgFrame.setVisible(False)
            
    def _delWidgets(self):
        """
        Delete dynamically created subwidgets
        """
        widgetList = self.dynWdgFrame.findChildren(
                                            (QtGui.QComboBox,QtGui.QLineEdit))
#       widgetListNames = [w.objectName() for w in widgetList]

        for w in widgetList:
            self.hLayout2.removeWidget(w)   # remove widget from layout
            w.deleteLater()             # tell Qt to delete object when the 
                                        # method has completed
            del w                       # not really needed?

#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = SelectFilter(DEBUG = True)
    form.show()
   
    app.exec_()

