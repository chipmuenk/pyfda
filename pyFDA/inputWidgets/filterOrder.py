# -*- coding: utf-8 -*-
"""
Widget for selecting / entering manual or minimum filter order

@author: juliabeike
Datum:12.11.2013
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui

# import databroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import databroker as db

class FilterOrder(QtGui.QFrame):
    """
    Build and update widget for selecting either 
    - manual filter order, specified by an integer 
    - minimum ('min') filter order
    """
    
    def __init__(self, DEBUG = False):
        super(FilterOrder, self).__init__()
        self.DEBUG = DEBUG        
        self.initUI()

        
    def initUI(self):
        bfont = QtGui.QFont()
        ifont = QtGui.QFont()
  #      font.setPointSize(11)
        bfont.setBold(True)
        bfont.setWeight(75)
        ifont.setItalic(True)
        # Print subwidget title
        self.titleLabel = QtGui.QLabel("Filter Order")
        self.titleLabel.setFont(bfont)

        self.chkMin = QtGui.QRadioButton("Minimum",self)          
        self.spacer = QtGui.QSpacerItem(40,0,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.txtLabel = QtGui.QLabel("N = ")
        self.txtLabel.setFont(ifont)
        self.txtManual=QtGui.QLineEdit(str(db.gD["curSpecs"]['N']),self)
 #       self.txtManual.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        #----------------------------------------------------------------------
        # Construct widget layout

        vbox = QtGui.QHBoxLayout()
        vbox.addWidget(self.chkMin)
        vbox.addItem(self.spacer)
        vbox.addWidget(self.txtLabel)

        vbox.addWidget(self.txtManual)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.titleLabel)
        layout.addItem(vbox)
        
        foFrame = QtGui.QFrame()
        foFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        foFrame.setLayout(layout)
        foFrame.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Minimum)
        
        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(foFrame)
        self.setLayout(mainLayout)
        
        
#        mainLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        
#        self.setLayout(layout)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs

        self.chkMin.clicked.connect(self.update)
        self.txtManual.editingFinished.connect(self.update)
        
        self.update() # initialize with default settings
        
    def update(self):
        # read list of available filter order methods from filterTree:
        foList = db.gD['filterTree'][db.gD['selFilter']['rt']]\
                [db.gD['selFilter']['ft']][db.gD['selFilter']['dm']].keys()
        if self.DEBUG: 
            print("=== filterOrder.update() ===")            
            print("foList", foList)

        if db.gD['selFilter']['fo'] in foList:
            fo = db.gD['selFilter']['fo'] # keep current setting
        else:
            fo = foList[0] # use first list entry from filterTree
            db.gD['selFilter']['fo'] = fo # and update 'selFilter'

        # Determine which subwidgets are __visible__
        self.txtLabel.setVisible("man" in foList)
        self.txtManual.setVisible("man" in foList)  
        self.chkMin.setVisible("min" in foList)            

        if self.DEBUG: print("fo[curFilt] =", fo)   

        # Determine which subwidgets are enabled
        if "min" in foList:
            if self.chkMin.isChecked() == True:
                # update if N has been changed outside this class
                self.txtManual.setText(str(db.gD["curSpecs"]["N"])) 
                self.txtManual.setEnabled(False)
                self.txtLabel.setEnabled(False)
                db.gD['selFilter'].update({"fo" : "min"})
            else:
                self.txtManual.setEnabled(True)
                self.txtLabel.setEnabled(True)
                db.gD['selFilter'].update({"fo" : "man"})
        else:
            self.txtLabel.setEnabled(fo == 'man')
            self.txtManual.setEnabled(fo == 'man')

        ordn = int(self.txtManual.text())
        db.gD["curSpecs"].update({"N" : ordn})
   
#------------------------------------------------------------------------------        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = FilterOrder()
    form.show()
    form.chkMin.setChecked(True)
    form.update()
    print(db.gD['selFilter']["fo"])
    form.chkMin.setChecked(False)
    form.update()
    print(db.gD['selFilter']["fo"])

    app.exec_()


   
        



 