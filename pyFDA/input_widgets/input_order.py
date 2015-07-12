# -*- coding: utf-8 -*-
"""
Widget for selecting / entering manual or minimum filter order

@author: Julia Beike, Christian Muenker, Michael Winkler
Datum: 20.01.2015
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb

class InputOrder(QtGui.QFrame):
    """
    Build and update widget for selecting either
    - manual filter order, specified by an integer
    - minimum ('min') filter order
    """
    
    sigSpecsChanged = pyqtSignal()

    def __init__(self, DEBUG = True):
        super(InputOrder, self).__init__()
        self.DEBUG = DEBUG
        self.dmLast = '' # design method from last call
        self.initUI()


    def initUI(self):
        """
        Initialize User Interface for filter order widget
        """        
        
        title = "Filter Order"

        bfont = QtGui.QFont()
        ifont = QtGui.QFont()
  #      font.setPointSize(11)
        bfont.setBold(True)
        bfont.setWeight(75)
        ifont.setItalic(True)

        # Print Widget title
        self.lblTitle = QtGui.QLabel(title)
        self.lblTitle.setFont(bfont)

        self.chkMin = QtGui.QRadioButton("Minimum",self)
        self.spacer = QtGui.QSpacerItem(20,0,
                        QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.lblOrder = QtGui.QLabel("N = ")
        self.lblOrder.setFont(ifont)
        self.ledOrder=QtGui.QLineEdit(str(fb.fil[0]['N']),self)
 #       self.ledOrder.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        #----------------------------------------------------------------------
        # Construct widget layout
        # ---------------------------------------------------------------------
        #  Dynamically created subwidgets
        self.layHDynWdg = QtGui.QHBoxLayout()
        self.frmDynWdg = QtGui.QFrame()
        self.frmDynWdg.setLayout(self.layHDynWdg)        
        self.frmDynWdg.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)

        #  All subwidgets, including dynamically created ones
        self.layHAllWdg = QtGui.QHBoxLayout()
        self.layHAllWdg.addWidget(self.chkMin)
        self.layHAllWdg.addItem(self.spacer)
        self.layHAllWdg.addWidget(self.lblOrder)
        self.layHAllWdg.addWidget(self.ledOrder)
        self.layHAllWdg.addWidget(self.frmDynWdg)

        self.frmFo = QtGui.QFrame()
        self.frmFo.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.frmFo.setLayout(self.layHAllWdg)
        self.frmFo.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Minimum)

        layVMain = QtGui.QVBoxLayout() # widget main layout
        layVMain.addWidget(self.lblTitle)
        layVMain.addWidget(self.frmFo)
        layVMain.setContentsMargins(1,1,1,1)

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chkMin.clicked.connect(self.storeEntries)
        self.ledOrder.editingFinished.connect(self.storeEntries)
        #----------------------------------------------------------------------

        self.loadEntries() # initialize with default settings
        
    def updateUI(self):
        """
        (Re)Create filter order widget depending on the available 
        options ('min', 'man') of the selected design method 
        """

        # read list of available filter order [fo] methods for current 
        # design method [dm] from filTree:
        foList = fb.filTree[fb.fil[0]['rt']]\
            [fb.fil[0]['ft']][fb.fil[0]['dm']].keys()
        if self.DEBUG:
            print("=== InputOrder.update() ===")
            print("foList", foList)

        # is currently selected fo setting available for (new) dm ?
        if fb.fil[0]['fo'] in foList:
            self.fo = fb.fil[0]['fo'] # keep current setting
        else:
            self.fo = foList[0] # use first list entry from filterTree
            fb.fil[0]['fo'] = self.fo # and update fo method

        # update dynamic (i.e. defined in filter design routine) subwidgets
        self._updateDynWidgets()

        # Determine which subwidgets are __visible__
        self.lblOrder.setVisible('man' in foList)
        self.ledOrder.setVisible('man' in foList)
        self.chkMin.setVisible('min' in foList)


    def loadEntries(self):
        """
        Read filter order settings from global dictionary and update the UI 
        correspondingly
        """
        self.updateUI()
        
        self.chkMin.setChecked(fb.fil[0]['fo'] == 'min')
        self.ledOrder.setText(str(fb.fil[0]['N']))
        self.ledOrder.setEnabled(not self.chkMin.isChecked())
        self.lblOrder.setEnabled(not self.chkMin.isChecked())
        

    def storeEntries(self):
        """
        Write text entries and checkbutton setting for filter order to dict
        """

        # Determine which subwidgets are _enabled_
        if self.chkMin.isVisible():
            self.ledOrder.setEnabled(not self.chkMin.isChecked())
            self.lblOrder.setEnabled(not self.chkMin.isChecked())
            
            if self.chkMin.isChecked() == True:
                # update in case N has been changed outside this class
                self.ledOrder.setText(str(fb.fil[0]['N']))
                fb.fil[0].update({'fo' : 'min'})
                
            else:
                fb.fil[0].update({'fo' : 'man'})
                
        else:
            self.lblOrder.setEnabled(self.fo == 'man')
            self.ledOrder.setEnabled(self.fo == 'man')

        ordn = int(abs(float(self.ledOrder.text())))
        self.ledOrder.setText(str(ordn))
        fb.fil[0].update({'N' : ordn})
        
        self.sigSpecsChanged.emit() # -> input_all
        

    def _updateDynWidgets(self):
        """
        Delete dynamically (i.e. within filter design routine) created subwidgets 
        and create new ones, depending on requirements of filter design algorithm
        
        This does NOT work when the subwidgets to be deleted and created are
        identical, as the deletion is only performed when the current scope has
        been left (?)! Hence, it is necessary to skip this method when the new
        design method is the same as the old one.
        
        """

        if fb.fil[0]['dm'] != self.dmLast:
                
            # Find "old" dyn. subwidgets and delete them:
            widgetList = self.frmDynWdg.findChildren(
                                                (QtGui.QComboBox,QtGui.QLineEdit))
            for w in widgetList:
                self.layHDynWdg.removeWidget(w)   # remove widget from layout
                w.deleteLater()             # tell Qt to delete object when the
                                            # method has completed
                del w                       # not really needed?
    
            # Try to create "new" dyn. subwidgets:
            if hasattr(fb.filObj, 'wdg'):
                try:
                    if 'fo' in fb.filObj.wdg:
                        a = getattr(fb.filObj, fb.filObj.wdg['fo'])
                        self.layHDynWdg.addWidget(a)
                        self.layHDynWdg.setContentsMargins(0,0,0,0)
                        self.frmDynWdg.setVisible(a != None)
                except AttributeError as e: # no attribute 'wdg'
                    print("fo.updateWidgets:", e)
                    self.frmDynWdg.setVisible(False)

        self.dmLast = fb.fil[0]["dm"]


#------------------------------------------------------------------------------
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = InputOrder()
    form.show()
    form.chkMin.setChecked(True)
    form.update()
    print(fb.fil[0]['fo'])
    form.chkMin.setChecked(False)
    form.update()
    print(fb.fil[0]['fo'])

    app.exec_()
