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
    Construct Comboboxes for FilterType (IIR, FIR, ...) and DesignMethod 
    (Equiripple, Butterworth etc.). When comboFilterType is triggered, 
    reconstruct comboDesignMethod
    """
    
    def __init__(self):
        super(DesignMethod, self).__init__()        
        self.initUI()
        
        
    def initUI(self): 
#        self.designType =""
#        self.designFilter =""
      
        # TODO: read this lists from a file instead of hard coding it
        self.dict_FilterTypeDesignMethod = \
        {"IIR": ["Butterworth","Chebychev 1", "Chebychev 2", "Elliptic"],
         "FIR": ['Equiripple','Least-squares','Window']}

        """
        Erzeuge ComboBox zur Auswahl des Filtertyps (IIR, FIR, ...)       
        """
        self.comboFilterType=QtGui.QComboBox(self)
#        self.comboFilterType.addItems(["IIR","FIR"])
        for dm in self.dict_FilterTypeDesignMethod:
                    self.comboFilterType.addItem(dm)
        
        """
        Create Combobox for the DesignMethode and populate it via
        set_FilterType()    
        """
        self.comboDesignMethod=QtGui.QComboBox(self)
        self.set_FilterType()



        #------------------------------------------------------------
        # Signals & Slots       
        #
        # Auswahl IIR / FIR: Rufe set_FilterType auf, um die Combobox für
        # die FilterDesignMethode neu zu generieren
        
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
        Triggered when comboFilterType (IIR, FIR, ...) is changed: Reconstruct 
        comboDesignMethod (Equiripple, Butterworth, ...)
        """
        self.comboDesignMethod.clear()            
        curDM = str(self.comboFilterType.currentText())
        self.comboDesignMethod.addItems(self.dict_FilterTypeDesignMethod[curDM])

        
    def get(self):
        """
        Return the currently selected filterType and designMethod
        """
        ft = self.comboFilterType.currentText()
        dm = self.comboDesignMethod.currentText()
        return{"Filtertyp":ft,"Design_Methode": dm}  

#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = DesignMethod()
    form.show()
   
    app.exec_()

