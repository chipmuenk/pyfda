# -*- coding: utf-8 -*-
"""
input_filter.py
---------------
Subwidget for selecting the filter, consisting of combo boxes for:
- Response Type (LP, HP, Hilbert, ...)
- Filter Type (IIR, FIR, CIC ...)
- DesignMethod (Butterworth, ...)

@author: Julia Beike, Christian Münker, Michael Winkler
Datum: 4.12.2014
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui

# TODO: Add subwidgets, depending on filterSel parameters
# TODO:  index = myComboBox.findText('item02') 

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb
from filter_tree_builder import FilterTreeBuilder

class SelectFilter(QtGui.QWidget):
    """
    Construct combo boxes for selecting the filter, consisting of:
      - Response Type (LP, HP, Hilbert, ...)
      - Filter Type (IIR, FIR, CIC ...)
      - DesignMethod (Butterworth, ...)
    """

    def __init__(self, DEBUG = False):
        super(SelectFilter, self).__init__()
        self.DEBUG = DEBUG
        # initialize the FilterTreeBuilder class with the filter directory and
        # the filter file
        self.ftb = FilterTreeBuilder('filter_design', 'init.txt',
                                    commentChar = '#', DEBUG = DEBUG) #
        self.filter_initialized = False

        self.initUI()
        
        self.setResponseType()


    def initUI(self):
        """
        Initialize UI with comboboxes for selecting filter
        """
#-----------------------------------------------------------------------------
#        see filterbroker.py for structure and content of "filterTree" dict
#-----------------------------------------------------------------------------

        #----------------------------------------------------------------------
        # Create combo boxes
        # - cmbResponseType for selecting response type rt (LP, HP, ...)
		# - cmbFilterType for selection of filter type (IIR, FIR, ...)
		# - cmbDesignMethod for selection of design method (Chebychev, ...)
		# and populate them from the "filterTree" dict either directly or by
		# calling setResponseType() :

        self.cmbResponseType=QtGui.QComboBox(self)
        self.cmbResponseType.setToolTip("Select filter response type.")
        self.cmbFilterType=QtGui.QComboBox(self)
        self.cmbFilterType.setToolTip("Select the kind of filter (recursive, transversal, ...).")
        self.cmbDesignMethod=QtGui.QComboBox(self)
        self.cmbDesignMethod.setToolTip("Select the actual filter design method.")



        # Adapt combobox size dynamically to largest element
        self.cmbResponseType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbFilterType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbDesignMethod.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        # Translate short response type ("LP") to displayed names ("Lowpass")
        # (correspondence is defined in filterbroker.py) and populate combo box:
        for rt in fb.filTree:
            self.cmbResponseType.addItem(fb.gD['rtNames'][rt], rt)
        self.cmbResponseType.setCurrentIndex(0) # set initial index


        """
        LAYOUT
        """
        # see Summerfield p. 278
        self.layHDynWdg = QtGui.QHBoxLayout() # for additional subwidgets
        self.frmDynWdg = QtGui.QFrame() # collect subwidgets in frame (no border)
        
        """Edit WinMic"""
        #Verschiebt alles was in dem Frame dargestellt wird, so wird Platz gespart.
        #TODO: Unsauber?
#        self.frmDynWdg.setContentsMargins(-10,-9,-10,-9)
        self.frmDynWdg.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        
        #Die folgende Zeile dient nur dazu um den 2. Frame, welcher für für dynamische
        #subwidgets ist anzuzeigen.
        #TODO: Zeile löschen fals Sie hier vergessen wird.
        
        #self.frmDynWdg.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Raised)
        """END"""
        
        self.frmDynWdg.setLayout(self.layHDynWdg)

        layHStdWdg = QtGui.QHBoxLayout() # container for standard subwidgets
        
        spacer = QtGui.QSpacerItem(1, 0, QtGui.QSizePolicy.Expanding, 
                                         QtGui.QSizePolicy.Fixed)
        
        layHStdWdg.addWidget(self.cmbResponseType)# QtCore.Qt.AlignLeft)
        
        layHStdWdg.addItem(spacer)
        
        layHStdWdg.addWidget(self.cmbFilterType)
        
        layHStdWdg.addItem(spacer)        
        
        layHStdWdg.addWidget(self.cmbDesignMethod)

        # stack standard + dynamic subwidgets vertically:
        layVAllWdg = QtGui.QVBoxLayout()

        layVAllWdg.addLayout(layHStdWdg)
        layVAllWdg.addWidget(self.frmDynWdg)
        
#        """EDIT WinMic"""
#        #Fals Windowes ausgewählt wird, verhindert der Spacer das nach unten abtauchen
#        #des neuen Subwidgets
#        spacer = QtGui.QSpacerItem(0, 1, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
#        layVAllWdg.addItem(spacer)
#        """END"""

        self.frmMain = QtGui.QFrame()
        self.frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.frmMain.setLayout(layVAllWdg)

        layHMain = QtGui.QHBoxLayout()
        layHMain.addWidget(self.frmMain)
        layHMain.setContentsMargins(0,0,0,0)

        self.setLayout(layHMain)
#        layHMain.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        
        #------------------------------------------------------------
        # SIGNALS & SLOTS
        #
        # Connect comboBoxes and setters

        self.cmbResponseType.activated.connect(self.setResponseType) # 'LP'
        self.cmbFilterType.activated.connect(self.setFilterType) #'IIR'
        self.cmbDesignMethod.activated.connect(self.setDesignMethod) #'cheby1'


    def setResponseType(self):
        """
        Triggered when cmbResponseType (LP, HP, ...) is changed:
        Copy selection to self.rt and fb.fil[0] and reconstruct filter type combo

        If previous filter type (FIR, IIR, ...) exists for new rt, set the 
        filter type combo box to the old setting 
        """
        # cmbBox.currentText() shows full text ('Lowpass'), 
        # itemData only abbreviation ('LP')
        self.rtIdx = self.cmbResponseType.currentIndex()
        self.rt = str(self.cmbResponseType.itemData(self.rtIdx))

        fb.fil[0]['rt'] = self.rt # copy selected rt setting to filter dict

        # rebuild filter type combobox entries for new rt setting 
        # The combobox is populated with the "long name", the internal name
        # is stored in comboBox.itemData               
        self.cmbFilterType.clear()
        self.cmbFilterType.addItems(
            list(fb.filTree[self.rt].keys())) # explicit list() needed for Py3

        # get list of available filter types for new rt
        ftList = fb.filTree[self.rt].keys() 
        # Is last filter type (e.g. IIR) in list for new rt? 
        # And has the widget been initialized?
        if fb.fil[0]['ft'] in ftList and self.filter_initialized:
            ft_idx = self.cmbFilterType.findText(fb.fil[0]['ft'])
            self.cmbFilterType.setCurrentIndex(ft_idx) # yes, set same ft as before
        else:
            self.cmbFilterType.setCurrentIndex(0)     # no, set index 0        
        
        self.setFilterType()

    def setFilterType(self):
        """"
        Triggered when cmbFilterType (IIR, FIR, ...) is changed:
        Copy selected setting to self.ft and (re)construct design method combo,
        adding displayed text (e.g. "Chebychev 1") and hidden data (e.g. "cheby1")
        """
        # cmbBox.currentText() has full text ('IIR'), 
        # itemData only abbreviation ('IIR')
        ftIdx = self.cmbFilterType.currentIndex()
        self.ft = str(self.cmbFilterType.currentText())
        # TODO: This line gives back key 'None' causing a crash downstream
        #self.ft = str(self.cmbFilterType.itemData(ftIdx))

        fb.fil[0]['ft'] = self.ft

        # Rebuild design method combobox entries for new ft setting:
        # The combobox is populated with the "long name", the internal name
        # is stored in comboBox.itemData        
        self.cmbDesignMethod.clear()
        
        # TODO: The following line dumps a core when the key does not exist !!!
        for dm in fb.filTree[self.rt][self.ft]:
            self.cmbDesignMethod.addItem(fb.gD['dmNames'][dm], dm)
                       
        # get list of available design methods for new ft
        dmList = fb.filTree[self.rt][self.ft].keys() 
        if self.DEBUG: 
            print("dmlist", dmList)
            print(fb.fil[0]['dm'])
            
            

            
        # Is previous design method (e.g. ellip) in list for new ft? 
        # And has the widget been initialized?
        if fb.fil[0]['dm'] in dmList and self.filter_initialized:
            dm_idx = self.cmbDesignMethod.findText(fb.gD['dmNames'][fb.fil[0]['dm']])
            print("dm_idx", dm_idx)
            self.cmbDesignMethod.setCurrentIndex(dm_idx) # yes, set same dm as before
        else:
            self.cmbDesignMethod.setCurrentIndex(0)     # no, set index 0  


        self.setDesignMethod()

    def setDesignMethod(self):
        """
        Triggered when cmbDesignMethod (cheby1, ...) is changed:
        Copy selected setting to self.dm # TODO: really needed?
        """
        dmIdx = self.cmbDesignMethod.currentIndex()
        self.dm = str(self.cmbDesignMethod.itemData(dmIdx))
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
                        fb.filTree[self.rt][self.ft][self.dm].keys():
            fb.fil[0].update({'fo':{}})
            fb.fil[0]['fo'] \
                = fb.filTree[self.rt][self.ft][self.dm].keys()[0]

        if self.DEBUG:
            print("=== InputFilter.setDesignMethod ===")
            print("selFilter:", fb.fil[0])
            print("filterTree[dm] = ", fb.filTree[self.rt][self.ft]\
                                                            [self.dm])
            print("filterTree[dm].keys() = ", fb.filTree[self.rt][self.ft]\
                                                            [self.dm].keys())


        self.filter_initialized = True
        
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
                self.layHDynWdg.addWidget(a, stretch = 1)
                self.layHDynWdg.setContentsMargins(0,0,0,0)
#                self.a.setContentsMargins(0,10,0,0)
#                self.layHDynWdg.addStretch()
                self.frmDynWdg.setVisible(a != None)
            
        except AttributeError as e:
            print("sf.updateWidgets:",e)
            self.frmDynWdg.setVisible(False)

    def _delWidgets(self):
        """
        Delete dynamically created subwidgets
        """
        widgetList = self.frmDynWdg.findChildren(
                                            (QtGui.QComboBox,QtGui.QLineEdit))
#       widgetListNames = [w.objectName() for w in widgetList]

        for w in widgetList:
            self.layHDynWdg.removeWidget(w)   # remove widget from layout
            w.deleteLater()             # tell Qt to delete object when the
                                        # method has completed
            del w                       # not really needed?

#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = SelectFilter()
    form.show()

    app.exec_()

