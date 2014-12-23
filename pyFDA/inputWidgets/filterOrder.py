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
    Widget for selecting either 
    - manual filter order, specified by an integer 
    - minimum ('min') filter order
    """
    
    def __init__(self, DEBUG = False):
        super(FilterOrder, self).__init__()        
        self.initUI()

        
    def initUI(self):
        bfont = QtGui.QFont()
        ifont = QtGui.QFont()
  #      font.setPointSize(11)
        bfont.setBold(True)
        bfont.setWeight(75)
        ifont.setItalic(True)
     
        self.titleLabel = QtGui.QLabel("Filter Order")
        self.titleLabel.setFont(bfont)
        self.chkMin = QtGui.QRadioButton("Minimum",self)
        self.chkMin.setChecked(db.gD["curFilter"]['fo']=='min') 
        self.spacer = QtGui.QSpacerItem(40,0,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.txtLabel = QtGui.QLabel("N = ")
        self.txtLabel.setFont(ifont)
        
        self.txtManual=QtGui.QLineEdit(str(db.gD["curSpecs"]['N']),self)
 #       self.txtManual.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        """
        LAYOUT 
        """
        vbox = QtGui.QHBoxLayout()
        vbox.addWidget(self.chkMin)
        vbox.addItem(self.spacer)
        vbox.addWidget(self.txtLabel)

        vbox.addWidget(self.txtManual)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.titleLabel)
        layout.addItem(vbox)
        self.setLayout(layout)

        """
        SIGNALS & SLOTs
        """
#        self.chkManual.clicked.connect(self.enableTxt)
        self.chkMin.clicked.connect(self.update)
        self.txtManual.textEdited.connect(self.update)
        
        self.update() # initialize with default settings
        
    def update(self):
        """
        Text input is only possible wenn "Min" is unchecked
        """
        ordn = int(self.txtManual.text())
        db.gD["curSpecs"].update({"N" : ordn})
        if self.chkMin.isChecked() == True:
            self.txtManual.setEnabled(False)
            self.txtLabel.setEnabled(False)
            db.gD["curFilter"].update({"fo" : "min"})
        else:
            self.txtManual.setEnabled(True)
            self.txtLabel.setEnabled(True)
            db.gD["curFilter"].update({"fo" : "man"})
   
#------------------------------------------------------------------------------        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = FilterOrder()
    form.show()
    form.chkMin.setChecked(True)
    form.update()
    print(db.gD["curFilter"]["fo"])
    form.chkMin.setChecked(False)
    form.update()
    print(db.gD["curFilter"]["fo"])

    app.exec_()


   
        



 