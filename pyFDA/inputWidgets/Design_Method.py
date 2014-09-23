# -*- coding: utf-8 -*-
"""
Auswahl von DesignTyp,FilterMethode 
@author: Julia Beike
Datum:14.11.2013
"""
import sys
from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

class Design_Method(QtGui.QWidget):
    
    def __init__(self):
        super(Design_Method, self).__init__()        
        self.initUI()
        
        
    def initUI(self): 
        self.design_typ=""
        self.design_filter=""
    
      
        
        self.list_FilterMethod_IIR=["Butterworth","Chebychev 1", 
        "Chebychev 2", "Elliptic"]

        self.list_FilterMethod_FIR=['Equiripple','Least-squares','Window']
        



        """
        ComboBox zur Auswahl des Filtertyps        
        """
        self.combo_Filtertyp=QtGui.QComboBox(self)
        self.combo_Filtertyp.addItems(["IIR","FIR"])
        
        """
        Combobox zur Auswahl des Filtermethode FIR       
        """
        
        self.combo_FilterMethod=QtGui.QComboBox(self)
        self.combo_FilterMethod.addItems(self.list_FilterMethod_IIR)


        """
        SIGNALE       
        """

        self.connect(self.combo_Filtertyp,SIGNAL('activated(QString)'),self.sel_FilterMethod)
        
        """
        LAYOUT      
        """

        layout=QtGui.QGridLayout()
        layout.addWidget(self.combo_Filtertyp,0,0)
        layout.addWidget(self.combo_FilterMethod,0,1)

        self.setLayout(layout)
        
        
    def sel_FilterMethod(self):
        if  str(self.combo_Filtertyp.currentText())=="IIR":
            self.combo_FilterMethod.clear()
            self.combo_FilterMethod.addItems(self.list_FilterMethod_IIR)
        else:
            self.combo_FilterMethod.clear()
            self.combo_FilterMethod.addItems(self.list_FilterMethod_FIR)

        
    def  get(self):
        """
        Rückgabe der Ausgewählten Filtermethode
        """
        f=self.combo_Filtertyp.currentText()
        a=self.combo_FilterMethod.currentText()
        return{"Filtertyp":f,"Design_Methode": a}  
    
     
   
 
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = Design_Method()
    form.show()
   
    app.exec_()

