# -*- coding: utf-8 -*-
"""
Auswahl von DesignTyp,FilterMethode und Window 
@author: juliabeike
Datum:12.11.2013
"""

import sys
from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

class ResponseType(QtGui.QWidget):
    
    def __init__(self):
        super(ResponseType, self).__init__()        
        self.initUI()
        
        
    def initUI(self): 
        



        """
        Radio Buttons zur Auswahl des REsponse Type        
        """


       # self.group.exclusive(True)
        self.combo=QtGui.QComboBox(self)
        self.combo.addItems(["Lowpass","Highpass","Bandpass","Bandstop"])

        """
        LAYOUT      
        """
        
        layout=QtGui.QGridLayout()
        layout.addWidget( self.combo,0,0)

        self.setLayout(layout)
        

         
    def  get(self):
        """
        Rückgabe des aktuellen Filtertyps
        """
        dic={"Lowpass":"LP","Highpass":"HP","Bandpass":"BP","Bandstop":"BS"}
        n=self.combo.currentText()
        print n
        a=dic[str(n)]
        return{"Response Type":a}
          
            
   
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = ResponseType()
    form.show()
    a=form.get()
    print a
    app.exec_()


   
        



 