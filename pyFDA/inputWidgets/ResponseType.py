# -*- coding: utf-8 -*-
"""
Auswahl des Response Types (Lowpass, Highpass, ...)

@author: juliabeike
Datum:12.11.2013
"""

import sys
from PyQt4 import QtGui

DEBUG = True

class ResponseType(QtGui.QWidget):
    """
    Widget for entering the filter response type (lowpass, highpass, ...)
    """
    
    def __init__(self,rt, debug = False):
        super(ResponseType, self).__init__()        
        self.initUI(rt)
        
        
    def initUI(self,rt, debug = False): 
        """
        Combo Box zur Auswahl des Response Types        
        """
       # self.group.exclusive(True)
        self.combo=QtGui.QComboBox(self)
        self.combo.addItems(rt)

        """
        LAYOUT      
        """       
        layout=QtGui.QGridLayout()
        layout.addWidget(self.combo,0,0)

        self.setLayout(layout)
        
         
    def  get(self):
        """
        Rückgabe des aktuellen Filtertyps
        """
        dic={"Lowpass":"LP","Highpass":"HP","Bandpass":"BP","Bandstop":"BS"}
        curText = self.combo.currentText()
        a=dic[str(curText)]
        if DEBUG:
            print("-------------------------")
            print("ResponseType.py: ") 
            print("-------------------------")
            print("FilterTyp:" ,curText)
        return{"Response Type":a}
          
#------------------------------------------------------------------------------            
   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = ResponseType(["Lowpass","Highpass","Bandpass","Bandstop"])
    form.show()
    a=form.get()
    print a
    app.exec_()


   
        



 