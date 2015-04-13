# -*- coding: utf-8 -*-
"""
Widget for selecting / entering manual or minimum filter order

@author: Julia Beike, Christian Muenker, Michael Winkler
Datum: 20.01.2015
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui

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

    def __init__(self, DEBUG = False):
        super(InputOrder, self).__init__()
        self.DEBUG = DEBUG
        self.dmLast = '' # design method from last call
        self.initUI()



    def initUI(self):

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
        
        """EDIT WinMic"""
        #Negativer Offset für fensterbeginne innerhalt des neuen Frames (somit verschwindet der ramen)
        #TODO: Unsauber?
        self.frmDynWdg.setContentsMargins(-10,-9,-10,-9)
        self.frmDynWdg.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
#        #self.frmDynWdg.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Raised)
        """END"""

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
#        layVMain.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs

        self.chkMin.clicked.connect(self.updateEntries)
        self.ledOrder.editingFinished.connect(self.updateEntries)

        self.updateEntries() # initialize with default settings

    def updateEntries(self):
        """
        Read / write text entries and checkbutton for filter order
        """
        # read list of available filter order methods from filterTree:
        foList = fb.filTree[fb.fil[0]['rt']]\
                [fb.fil[0]['ft']][fb.fil[0]['dm']].keys()
        if self.DEBUG:
            print("=== InputOrder.update() ===")
            print("foList", foList)

        if fb.fil[0]['fo'] in foList:
            fo = fb.fil[0]['fo'] # keep current setting
        else:
            fo = foList[0] # use first list entry from filterTree
            fb.fil[0]['fo'] = fo # and update 'selFilter'

        if self.DEBUG: print("fo[selFilter] =", fo)

        if fb.fil[0]['dm'] != self.dmLast:
            self.updateWidgets()

        # Determine which subwidgets are __visible__
        self.lblOrder.setVisible('man' in foList)
        self.ledOrder.setVisible('man' in foList)
        self.chkMin.setVisible('min' in foList)

        # When design method has changed, delete subwidgets referenced from
        # from previous filter design method and create new ones (if needed)

        # Determine which subwidgets are _enabled_
        if 'min' in foList:
            if self.chkMin.isChecked() == True:
                # update in case N has been changed outside this class
                self.ledOrder.setText(str(fb.fil[0]['N']))
                self.ledOrder.setEnabled(False)
                self.lblOrder.setEnabled(False)
                fb.fil[0].update({'fo' : 'min'})
            else:
                self.ledOrder.setEnabled(True)
                self.lblOrder.setEnabled(True)
                fb.fil[0].update({'fo' : 'man'})
        else:
            self.lblOrder.setEnabled(fo == 'man')
            self.ledOrder.setEnabled(fo == 'man')

        ordn = int(self.ledOrder.text())
        fb.fil[0].update({'N' : ordn})
        self.dmLast = fb.fil[0]["dm"]

    def updateWidgets(self):
        self._delWidgets()
        try:
            if 'fo' in fb.filObj.wdg:
                a = getattr(fb.filObj, fb.filObj.wdg['fo'])
                self.layHDynWdg.addWidget(a)
                self.frmDynWdg.setVisible(a != None)
        except AttributeError as e: # no attribute 'wdg'
            print("fo.updateWidgets:", e)
            self.frmDynWdg.setVisible(False)

    def _delWidgets(self):
        """
        Delete all dynamically (i.e. by filter design routine) created widgets
        """
        widgetList = self.frmDynWdg.findChildren(
                                            (QtGui.QComboBox,QtGui.QLineEdit))
        for w in widgetList:
            self.layHDynWdg.removeWidget(w)   # remove widget from layout
            w.deleteLater()             # tell Qt to delete object when the
                                        # method has completed
            del w                       # not really needed?

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
