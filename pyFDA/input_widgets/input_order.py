# -*- coding: utf-8 -*-
"""
Widget for selecting / entering manual or minimum filter order

@author: juliabeike, Christian Muenker
Datum: 20.01.2015
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
        self.titleLabel = QtGui.QLabel(title)
        self.titleLabel.setFont(bfont)

        self.chkMin = QtGui.QRadioButton("Minimum",self)          
        self.spacer = QtGui.QSpacerItem(20,0,
                        QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.txtLabel = QtGui.QLabel("N = ")
        self.txtLabel.setFont(ifont)
        self.txtManual=QtGui.QLineEdit(str(fb.fil[0]['N']),self)
 #       self.txtManual.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        #----------------------------------------------------------------------
        # Construct widget layout
        # ---------------------------------------------------------------------
        #  Dynamically created subwidgets
        self.hbox2 = QtGui.QHBoxLayout()        
        self.dynWdgFrame = QtGui.QFrame()
        self.dynWdgFrame.setLayout(self.hbox2)
        
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.chkMin)
        self.hbox.addItem(self.spacer)
        self.hbox.addWidget(self.txtLabel)
        self.hbox.addWidget(self.txtManual)
        self.hbox.addWidget(self.dynWdgFrame)
        
        self.foFrame = QtGui.QFrame()
        self.foFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.foFrame.setLayout(self.hbox)        
        self.foFrame.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Minimum)
        
        mainLayout = QtGui.QVBoxLayout() # widget main layout
        mainLayout.addWidget(self.titleLabel)
        mainLayout.addWidget(self.foFrame)
        self.setLayout(mainLayout)
#        mainLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs

        self.chkMin.clicked.connect(self.updateEntries)
        self.txtManual.editingFinished.connect(self.updateEntries)
        
        self.updateEntries() # initialize with default settings
        
    def updateEntries(self):
        """
        Read / write text entries and checkbutton for filter order
        """
        # read list of available filter order methods from filterTree:
        foList = fb.gD['filterTree'][fb.fil[0]['rt']]\
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
        self.txtLabel.setVisible('man' in foList)
        self.txtManual.setVisible('man' in foList)  
        self.chkMin.setVisible('min' in foList)

        # When design method has changed, delete subwidgets referenced from
        # from previous filter design method and create new ones (if needed)

        # Determine which subwidgets are _enabled_
        if 'min' in foList:
            if self.chkMin.isChecked() == True:
                # update in case N has been changed outside this class
                self.txtManual.setText(str(fb.fil[0]['N'])) 
                self.txtManual.setEnabled(False)
                self.txtLabel.setEnabled(False)
                fb.fil[0].update({'fo' : 'min'})
            else:
                self.txtManual.setEnabled(True)
                self.txtLabel.setEnabled(True)
                fb.fil[0].update({'fo' : 'man'})
        else:
            self.txtLabel.setEnabled(fo == 'man')
            self.txtManual.setEnabled(fo == 'man')

        ordn = int(self.txtManual.text())
        fb.fil[0].update({'N' : ordn})
        self.dmLast = fb.fil[0]["dm"]
        
    def updateWidgets(self):
        self._delWidgets()
        try:              
            if 'fo' in fb.filObj.wdg:
                a = getattr(fb.filObj, fb.filObj.wdg['fo'])
                self.hbox2.addWidget(a)
                self.dynWdgFrame.setVisible(a != None)
        except AttributeError as e: # no attribute 'wdg'
            print("fo.updateWidgets:", e)
            self.dynWdgFrame.setVisible(False)

    def _delWidgets(self):
        widgetList = self.dynWdgFrame.findChildren(
                                            (QtGui.QComboBox,QtGui.QLineEdit))
        for w in widgetList:
            self.hbox2.removeWidget(w)   # remove widget from layout
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


   
        



 