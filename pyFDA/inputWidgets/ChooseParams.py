# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 15:21:19 2013
Main Widget for entering filter specifications

@author: beike, Christian Münker
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
    
import SelectFilter, filterOrder, UnitBox


"""
Zur Eingabe aller Parameter und Einstellungen
"""


class ChooseParams(QtGui.QFrame):
    
    def __init__(self, DEBUG = True):
        super(ChooseParams, self).__init__() 
#        self.setStyleSheet("margin:5px; border:1px solid rgb(0, 0, 0); ")
#        self.setStyleSheet("background-color: rgb(255,0,0); margin:5px; border:1px solid rgb(0, 255, 0); ")

        self.DEBUG = DEBUG                                              
        self.initUI()
        """
        
        """        
    def initUI(self): 
        """
        Create all widgets:

        sf : Select Filter with response type rt (LP, ...), 
              filter type ft (IIR, ...), and design method dm (cheby1, ...)
        fo : Filter Order (numeric or 'min')
        fspec : Frequency Specifications 
        ms : Magnitude Specifications with the subwidgets
            txt : only text field for comments / instruction
            val : infostring (title), Label, value
            unt : unit, label, value

        """ 

        self.sf = SelectFilter.SelectFilter(DEBUG = False)
        self.fo = filterOrder.FilterOrder(DEBUG = True)
        # subwidget for Frequency Specs
        self.fspec = UnitBox.UnitBox(title = "Frequency Specifications",
                    units = ["Hz", "Normalize 0 to 1", "kHz", "MHz", "GHz"],
                    labels = ['fS', 'F_pb', 'F_sb'],
                    DEBUG = False)
        # subwidget for Amplitude Specs        
        self.aspec = UnitBox.UnitBox(title = "Amplitude Specifications",
                    units = ["dB","Squared"], labels = ["A_pb","A_sb"],
                    DEBUG = False)
        # subwidget for Weight Specs                                           
        self.wspec = UnitBox.UnitBox(
                    title = "Weight Specifications",
                    units = "", labels = ["W_pb","W_sb"],
                    DEBUG = False)
        
        self.msg = QtGui.QLabel(self)
        self.msg.setText("Enter a weight value for each band below")
        self.msg.setWordWrap(True)

        self.msg.setVisible(True)
        self.wspec.setVisible(True)
        self.aspec.setVisible(True)
        """
        LAYOUT      
        """
        self.layout=QtGui.QGridLayout()
        self.layout.addWidget(self.sf,0,0,1,2)  # Design method (IIR - ellip, ...)
        self.layout.addWidget(self.fo,1,0,1,2)  # Filter order
        self.layout.addWidget(self.fspec,2,0,1,2)  # Freq. specifications
        self.layout.addWidget(self.msg,3,0,1,2)  # Text message
        self.layout.addWidget(self.aspec,4,0)   # Amplitude specs
        self.layout.addWidget(self.wspec,4,1)   # Weight specs

        self.setLayout(self.layout)
        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        # Call chooseDesignMethod every time filter selection is changed: 
        self.fo.chkMin.clicked.connect(self.chooseDesignMethod)
        self.fo.txtManual.editingFinished.connect(self.update)
        self.sf.comboResponseType.activated.connect(self.chooseDesignMethod)
        self.sf.comboFilterType.activated.connect(self.chooseDesignMethod)
        self.sf.comboDesignMethod.activated.connect(self.chooseDesignMethod)

        self.chooseDesignMethod() # first time initialization
        
    def chooseDesignMethod(self):
        """
        Reads:  db.gD["curFilter"] (currently selected filter), extracting info
                from db.gD['filterTree']
        Writes:
        Depending on SelectFilter and frequency specs, the values of the 
        widgets fo, fspec are recreated. For widget ms, the visibility is changed
        as well.
        """

        # Read freq / amp / weight labels for current filter design
        rt = db.gD["curFilter"]["rt"]
        ft = db.gD["curFilter"]["ft"]
        dm = db.gD["curFilter"]["dm"]
        fo = db.gD["curFilter"]["fo"]  
        myLabels = db.gD['filterTree'][rt][ft][dm][fo]

        # build separate label lists according to the first letter
        self.freqLabels = [l for l in myLabels if l[0] == 'F']
        self.ampLabels = [l for l in myLabels if l[0] == 'A']
        self.weightLabels = [l for l in myLabels if l[0] == 'W']
        if self.DEBUG:
            print("=== chooseParams.chooseDesignMethod ===")
            print("curFilter:", db.gD["curFilter"])
            print('myLabels:', myLabels)
            print('ampLabels:', self.ampLabels)
            print('freqLabels:', self.freqLabels)
            print('weightLabels:', self.weightLabels)

        # pass new labels to widgets
        # disable (grey out) amp / weight labels if list is empty
        self.fo.update()
        self.fspec.set(newLabels = self.freqLabels) # update frequency spec labels
        self.aspec.setDisabled(self.ampLabels == [])
        self.aspec.set(newLabels = self.ampLabels)
        self.wspec.setDisabled(self.weightLabels == []) 
        self.wspec.set(newLabels = self.weightLabels)

        self.setLayout(self.layout)
        
        
#    def rebuildFrequFiltOrd(self,enMin=True):
#        """
#        Auxiliary function for updating frequency specifications and the 
#        frequency order widget
#        """
#        self.fspec.set(newLabels = self.freqLabels)
#        self.fo.chkMin.setEnabled(enMin)
        
#    def rebuildMag(self,string,lstA_W_T=[]):
#        """
#        Auxiliary function for updating magnitude specifications
#        """
        
#        if self.ampLabels == []:
#            self.aspec.setEnabled(False)
  
#        if self.weightLabels ==[]:
#            self.wspec.setEnabled(False)
#        if self.textField == "":
#            self.ms_txt.setVisible(False)
            

#        if string == "txt":  # only Info-Text
#            self.aspec.setVisible(False)
#            self.wspec.setVisible(False)
#            self.ms_txt.setText(self.infoText)
#            self.ms_txt.setVisible(True)
#        if string == "unit" : # create subwidget with unit + label
#            self.aspec.set(newLabels = self.ampLabels)#lstA_W_T[1])#, newDefaults = lstA_W_T[2])
#            self.aspec.setVisible(True)
#            self.wspec.setVisible(True)
#            self.ms_txt.setVisible(True)
            
    def get(self):
        """
        Update global dict db.gD["curSpecs"] with currently selected filter specs 
        """
    
#        ret = {}
#        db.gD["curFilter"]["fo"] # collect data from filter order widget
#        db.gD["curSpecs"].update(self.fspec.get()) # collect data from frequ. spec. widget
#        db.gD["curSpecs"].update(self.aspec.get()) # magnitude specs with unit
#        db.gD["curSpecs"].update(self.wspec.get()) # weight specs
        self.fo.update() # collect data from frequ. spec. widget
#        db.gD["curSpecs"] = {}
        self.fspec.update() # collect data from frequ. spec. widget
        self.aspec.update() # magnitude specs with unit
        self.wspec.update() # weight specs
        
            
        if self.DEBUG: print(db.gD["curSpecs"])
#        return self.params  
        
#------------------------------------------------------------------------------ 
   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = ChooseParams()
    form.show()
    form.get()
   
    app.exec_()


   
        



 