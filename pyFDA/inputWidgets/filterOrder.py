# -*- coding: utf-8 -*-
"""
Widget for selecting / entering manual or minimum filter order

@author: juliabeike
Datum:12.11.2013
"""
import sys
from PyQt4 import QtGui

class FilterOrder(QtGui.QWidget):
    """
    Widget for selecting either 
    - manual filter order, specified by an integer 
    - minimum ('min') filter order
    """
    
    def __init__(self):
        super(FilterOrder, self).__init__()        
        self.initUI()
        
        
    def initUI(self): 
     
        self.chkManual = QtGui.QRadioButton("Specify Order",self)
        self.chkMin = QtGui.QRadioButton("Minimum Order",self)
        self.group = QtGui.QButtonGroup(self)
        self.group.addButton(self.chkManual)
        self.group.addButton(self.chkMin)
        self.group.setExclusive(True)
        
        self.txtManual=QtGui.QLineEdit("10",self)
        self.txtManual.setEnabled(False)
        self.chkManual.setChecked(True) 
   
        """
        LAYOUT 
        """
        vbox = QtGui.QHBoxLayout()
        vbox.addWidget(self.chkManual)
        vbox.addWidget(self.txtManual)
        layout = QtGui.QVBoxLayout()
        layout.addItem(vbox)
        layout.addWidget(self.chkMin)
        self.setLayout(layout)
        """
        SIGNALS & SLOTs
        """
        self.chkManual.clicked.connect(self.enableTxt)
        self.chkMin.clicked.connect(self.enableTxt)
        
        self.enableTxt() # initialize with default settings
        
    def enableTxt(self):
        """
        Text input is only possible wenn "Manual" is checked
        """

        if self.chkManual.isChecked() == True:
            self.txtManual.setEnabled(True)
        else:
            self.txtManual.setEnabled(False)     
   
    def get(self):
         """
         Return either the entered filter order or 'min'
         """
         if self.chkManual.isChecked() == False:
             ordn = "min"
         else:
             ordn = int(self.txtManual.text())
         return {"Order": ordn}
         
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = widgetFilterOrder()
    form.show()
    form.chkManual.setChecked(True)
    t=form.get()
    print t
    form.chkMin.setChecked(True)
    t=form.get()
    print t
    app.exec_()


   
        



 