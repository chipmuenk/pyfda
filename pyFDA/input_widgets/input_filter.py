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
        # - cmbResponseType for selecting response type rt (LP, HP, ...)
		# - cmbFilterType for selection of filter type (IIR, FIR, ...)
		# - cmbDesignMethod for selection of design method (Chebychev, ...)
		# and populate them from the "filterTree" dict either directly or by
		# calling setResponseType() :

        #TODO: Hier wird 2x der Tooltip für self.cmbFilterType gesetzt?
        self.cmbResponseType=QtGui.QComboBox(self)
        self.cmbResponseType.setToolTip("Select filter response type.")
        self.cmbFilterType=QtGui.QComboBox(self)
        self.cmbFilterType.setToolTip("Select the kind of filter (recursive, transversal, ...).")
        self.cmbDesignMethod=QtGui.QComboBox(self)
        self.cmbFilterType.setToolTip("Select the actual filter design method.")


        """Edit WincMIC"""
        #Die ComboBox passt Ihre größe dynamisch dem längsten element an.
        self.cmbResponseType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbFilterType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbDesignMethod.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        
        """END"""
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
        
        """EDIT WinMic"""
#        
#        layHStdWdg.addItem(spacer)
        """END"""
        layHStdWdg.addWidget(self.cmbResponseType)# QtCore.Qt.AlignLeft)
        layHStdWdg.addWidget(self.cmbFilterType)
        layHStdWdg.addWidget(self.cmbDesignMethod)
        
        """EDIT WinMic"""
#        layHStdWdg.addItem(spacer)
        """END"""

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
        Copy selection to self.rt and fb.gD and reconstruct filter type combo
        """
        self.rtIdx = self.cmbResponseType.currentIndex()
        self.rt = str(self.cmbResponseType.itemData(self.rtIdx))

        fb.fil[0]['rt'] = self.rt # abbreviation
#        rt=fb.gD["rtNames"][self.rt] # full text
#        print(fb.filTree[self.rt].keys())
        #
        self.cmbFilterType.clear()
        self.cmbFilterType.addItems(
            list(fb.filTree[self.rt].keys())) # list() needed for Py3
        self.setFilterType()

    def setFilterType(self):
        """"
        Triggered when cmbFilterType (IIR, FIR, ...) is changed:
        Copy selected setting to self.ft and (re)construct design method combo,
        adding displayed text (e.g. "Chebychev 1") and hidden data (e.g. "cheby1")
        """
        self.ft = str(self.cmbFilterType.currentText())
        self.cmbDesignMethod.clear()

        for dm in fb.filTree[self.rt][self.ft]:
            self.cmbDesignMethod.addItem(fb.gD['dmNames'][dm], dm)

        fb.fil[0]['ft'] = self.ft
        self.setDesignMethod()

    def setDesignMethod(self):
        """
        Triggered when cmbDesignMethod (cheby1, ...) is changed:
        Copy selected setting to self.dm # TODO: really needed?
        """
        self.dmIdx = self.cmbDesignMethod.currentIndex()
        self.dm = str(self.cmbDesignMethod.itemData(self.dmIdx))
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
    form = SelectFilter(DEBUG = True)
    form.show()

    app.exec_()

