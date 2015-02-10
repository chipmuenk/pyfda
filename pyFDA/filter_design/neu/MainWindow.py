# -*- coding: utf-8 -*-
"""
Created on Sun Jan 05 12:47:52 2014

@author: Acer
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: beike
"""
from Widget import  Unit_Box,ResponseType,Design_Method,FilterOrder,Txt_Box
import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL


class MainWindow(QtGui.QWidget):
    
    def __init__(self,contr):
        super(MainWindow, self).__init__()     
        self.con=contr
        self.initUI()     
    
        #Alle "Eigenschaften" der verschiedenen Filtertypen
                                        
        
        
    def initUI(self): 
        """
        Anlegen aller Widgets 
        fs:= Frequency Specifications 
        ms:= Magnitude Specifications (wobei es hier verschiedene Typen gibt: tb:= text+Auswahlfelder; ub:= Einheit+ Auswahlfelder; txt:= nur Text)""" 
        self.rs=ResponseType.ResponseType() 
        self.dm=Design_Method.Design_Method()
        self.fo=FilterOrder.FilterOrder()
        self.fs=Unit_Box.Unit_Box(["Hz","Normalize 0 to 1","kHz","MHz","GHz"],['Fs','Fpass','Fstop'],[48000,9600,12000],"Frequenz")
       
        self.ms_tex=QtGui.QLabel(self)
        self.ms_tex.setText("Enter a weight value for each band below")
        self.ms_tex.setWordWrap(True)
        self.ms_ub=Unit_Box.Unit_Box(["DB","Squared"],["Apass","Astop"],[1,80],"Magnitude")
        self.ms_tb=Txt_Box.Txt_Box("Enter a weight value for each band below",["Wpass","Wstop"],[1,1])
        self.ms_last="tb"
        # alle Magnitude Widgets die nicht benötigt werden sind unsichtbar, aber trotzdem immer da!!
        self.ms_tex.setVisible(False)
        self.ms_ub.setVisible(False)
        self.ms_tb.setVisible(True)
        self.but_Design=QtGui.QPushButton("Design")
        """
        LAYOUT      
        """
        self.mainlayout=QtGui.QVBoxLayout()
        self.layout=QtGui.QGridLayout()
        self.layout.addWidget(self.rs,0,0)
        self.layout.addWidget(self.dm,1,0)
        self.layout.addWidget(self.fo,2,0)
        self.layout.addWidget(self.fs,3,0)
        self.layout.addWidget(self.ms_tex,4,0)
        self.layout.addWidget(self.ms_tb,5,0)
        self.layout.addWidget(self.ms_ub,6,0)
        self.mainlayout.addLayout(self.layout)
        self.mainlayout.addWidget(self.but_Design)
        self.setLayout(self.mainlayout)
        
        self.connect(self.but_Design,SIGNAL("clicked()"),self.get)
        self.connect(self.dm.combo_Filtertyp,SIGNAL('activated(QString)'),self.get)

    def get(self):    
        #need_Param(self,a="HP",b="cheby1",c="man"):
        param=self.con.need_Param(self.rs.get().get("Response Type"),str(self.dm.get().get("Design_Methode")),"man")        
        print param
   
