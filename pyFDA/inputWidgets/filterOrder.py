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
    
    def __init__(self, defaults = {'N':8, 'ord':'man'}):
        super(FilterOrder, self).__init__()        
        self.defaults = defaults
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
        self.chkMin.setChecked(self.defaults['ord']=='min') 
        self.spacer = QtGui.QSpacerItem(40,0,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.txtLabel = QtGui.QLabel("N = ")
        self.txtLabel.setFont(ifont)
        
        self.txtManual=QtGui.QLineEdit(str(self.defaults['N']),self)
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
        self.chkMin.clicked.connect(self.enableTxt)
        self.txtManual.textChanged.connect(self.get)
        
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
         Return either the entered filter order and 'min'/'man' as dict
         """
         ordn = int(self.txtManual.text())
         if self.chkMin.isChecked():
             return {"ord" : "min", "N" : ordn}       
         else:
             return {"ord": "man", "N": ordn}
         
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


   
        



 