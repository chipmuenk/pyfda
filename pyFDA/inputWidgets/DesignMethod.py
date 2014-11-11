# -*- coding: utf-8 -*-
"""
Auswahl von IIR /FIR (FilterType) und DesignMethod (Butterworth, ...)
@author: Julia Beike
Datum:14.11.2013
"""
import sys
from PyQt4 import QtGui
#from PyQt4.QtCore import SIGNAL

class DesignMethod(QtGui.QWidget):
    """
    Construct Comboboxes for FilterType (IIR, FIR) and DesignMethod (Equiripple,
    Butterworth etc.). When IIR / FIR is triggered, reconstruct comboDesignMethod
    """
    
    def __init__(self):
        super(DesignMethod, self).__init__()        
        self.initUI()
        
        
    def initUI(self): 
#        self.designType =""
#        self.designFilter =""
      
        # TODO: read this lists from a file instead of hard coding it
        self.list_DesignMethod_IIR=["Butterworth","Chebychev 1", 
        "Chebychev 2", "Elliptic"]
        self.list_DesignMethod_FIR=['Equiripple','Least-squares','Window']     

        """
        Erzeuge ComboBox zur Auswahl des Filtertyps (IIR / FIR)       
        """
        self.comboFilterType=QtGui.QComboBox(self)
        self.comboFilterType.addItems(["IIR","FIR"])
        
        """
        Erzeuge Combobox zur Auswahl der Filtermethode (beim Start: für IIR)       
        """
        self.comboDesignMethod=QtGui.QComboBox(self)
        self.comboDesignMethod.addItems(self.list_DesignMethod_IIR)


        """
        SIGNALE       
        """
        # Auswahl IIR / FIR: Rufe sel_FilterType auf, um die Combobox für
        # die FilterDesignMethode neu zu generieren
        
#        self.connect(self.combo_FilterType,SIGNAL('activated(QString)'),
#                     self.sel_FilterType)
        self.comboFilterType.activated.connect(self.set_FilterType)
        # TODO: Bei Auswahl einer DesignMethod muss die Liste der 
        # Responsetypen (HP, TP, ...) neu generiert werden:
#        self.combo_DesignMethod.activated.connect(sel_responseType)
        
        """
        LAYOUT      
        """

        layout=QtGui.QGridLayout()
        layout.addWidget(self.comboFilterType,0,0)
        layout.addWidget(self.comboDesignMethod,0,1)

        self.setLayout(layout)
        
        
    def set_FilterType(self):
        """
        Set FilterType (IIR / FIR) and reconstruct combo box for
        DesignMethod (Equiripple, Butterworth, ...)
        """
        if  str(self.comboFilterType.currentText())=="IIR":
            self.comboDesignMethod.clear()
            self.comboDesignMethod.addItems(self.list_DesignMethod_IIR)
        else:
            self.comboDesignMethod.clear()
            self.comboDesignMethod.addItems(self.list_DesignMethod_FIR)

        
    def get(self):
        """
        Return the currently selected filterType and designMethod
        """
        f=self.comboFilterType.currentText()
        a=self.comboDesignMethod.currentText()
        return{"Filtertyp":f,"Design_Methode": a}  

#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = DesignMethod()
    form.show()
   
    app.exec_()

