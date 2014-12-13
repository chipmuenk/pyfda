# -*- coding: utf-8 -*-
"""
Widget for selecting / entering manual or minimum filter order

@author: juliabeike
Datum:12.11.2013
"""
import sys
from PyQt4 import QtGui

class FilterOrder(QtGui.QFrame):
    """
    Widget for selecting either 
    - manual filter order, specified by an integer 
    - minimum ('min') filter order
    """
    
    def __init__(self):
        super(FilterOrder, self).__init__()        
        self.initUI()
        
        
    def initUI(self):
        bfont = QtGui.QFont()
        ifont = QtGui.QFont()
  #      font.setPointSize(11)
        bfont.setBold(True)
        bfont.setWeight(75)
        ifont.setItalic(True)
     
#        self.chkManual = QtGui.QRadioButton("Specify Order",self)
        self.titleLabel = QtGui.QLabel("Filter Order")
        self.titleLabel.setFont(bfont)
        self.chkMin = QtGui.QRadioButton("Minimum",self)
        self.spacer = QtGui.QSpacerItem(40,0,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.txtLabel = QtGui.QLabel("N = ")
        self.txtLabel.setFont(ifont)
        
        self.txtManual=QtGui.QLineEdit("10",self)
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
        
#        self.txtManual.setEnabled(False)
        self.chkMin.setChecked(True) 
        """
        SIGNALS & SLOTs
        """
#        self.chkManual.clicked.connect(self.enableTxt)
        self.chkMin.clicked.connect(self.enableTxt)
        
        self.enableTxt() # initialize with default settings
        
    def enableTxt(self):
        """
        Text input is only possible wenn "Min" is unchecked
        """

        if self.chkMin.isChecked() == True:
            self.txtManual.setEnabled(False)
            self.txtLabel.setEnabled(False)
        else:
            self.txtManual.setEnabled(True)
            self.txtLabel.setEnabled(True)
   
    def get(self):
         """
         Return either the entered filter order or 'min'
         """
         if self.chkMin.isChecked() == True:
             ordn = "min"
         else:
             ordn = int(self.txtManual.text())
         return {"Order": ordn}
         
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = FilterOrder()
    form.show()
#    form.chkMin.setChecked(True)
    t=form.get()
    print t
#    form.chkMin.setChecked(False)
    t=form.get()
    print t
    app.exec_()


   
        



 