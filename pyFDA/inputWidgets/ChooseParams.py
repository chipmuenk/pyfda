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

        # "Properties" of all filter types:
        self.choose_design_list=(
           ['firls','LP',['fS','F_pb','F_sb'],[48000,9600,12000],False,True,"unit",[[], ["W_pb","W_sb"],[1,1]],"Enter a weight value for each band below"],
           ['firls','HP',['fS','F_pb','F_sb'],[48000,9600,12000],False,True,"unit",[[], ["W_pb","W_sb"],[1,1]],"Enter a weight value for each band below"],
           ['firls','BP',['fS','F_sb','F_pb','F_sb2','F_pb2'],[48000,7200,9600,12000,14400],False,True,"unit",[[], ["W_sb","W_pb","W_sb2"],[1,1,1]],"Enter a weight value for each band below"],
           ['firls','BS',['fS','F_pb','F_sb','F_pb2','F_sb2'],[48000,7200,9600,12000,14400],False,True,"unit",[[], ["W_pb","W_sb","W_pb2"],[1,1,1]], "Enter a weight value for each band below"],
           ['equiripple','LP',['fS','F_pb','F_sb'],[48000,9600,12000],True,True,"unit",[[], ["W_pb","W_sb"],[1,1]],"Enter a weight value for each band below"],
           ['equiripple','HIL',['fS','F_pb','F_sb'],[48000,9600,12000],True,True,"unit",[[], ["W_pb","W_sb"],[1,1]],"Enter a weight value for each band below"],
           ['equiripple','HP',['fS','F_pb','F_sb'],[48000,9600,12000],True,True,"unit",[[], ["W_pb","W_sb"],[1,1]], "Enter a weight value for each band below"],
           ['equiripple','BP',['fS','F_sb','F_pb','F_sb2','F_pb2'],[48000,7200,9600,12000,14400],True,True,"unit",[[], ["W_sb","W_pb","W_sb2"],[1,1,1]], "Enter a weight value for each band below"],
           ['equiripple','BS',['fS','F_pb','F_sb','F_pb2','F_sb2'],[48000,7200,9600,12000,14400],True,True,"unit",[[], ["W_pb","W_sb","W_pb2"],[1,1,1]], "Enter a weight value for each band below"],     
           ['window','LP',['fS','Fc'],[48000,10800],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
           ['window','HP',['fS','Fc'],[48000,10800],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
           ['window','BP',['fS','Fc1','Fc2'],[48000,8400,13200],False,True, "txt",[], "The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
           ['window','BS',['fS','Fc1','Fc2'],[48000,8400,13200],False,True,"txt", [], "The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"], 
           ['butter','LP',['fS','Fc'],[48000,10800],True,True,"txt",[], "The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
           ['butter','HP',['fS','Fc'],[48000,10800],True,True,"txt",[], "The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
           ['butter','BP',['fS','Fc1','Fc2'],[48000,8400,13200],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
           ['butter','BS',['fS','Fc1','Fc2'],[48000,8400,13200],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
           ['ellip','LP',['fS','F_pb'],[48000,9600],True,True,"unit",[["dB","Squared"],["A_pb","A_sb"],[1,80]], ""],
           ['ellip','HP',['fS','F_pb'],[48000,14400],True,True,"unit",[["dB","Squared"],["A_pb","A_sb"],[1,80]], ""],
           ['ellip','BP',['fS','F_pb','F_pb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_sb","A_pb","A_sb2"],[60,1,80]], ""],
           ['ellip','BS',['fS','F_pb','F_pb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_pb1","A_sb","A_pb2"],[5,60,1]], ""],
           ['cheby1','LP',['fS','F_pb'],[48000,9600],True,True,"unit",[["dB","Squared"],["A_pb"],[1]], ""],
           ['cheby1','HP',['fS','F_pb'],[48000,14400],True,True,"unit",[["dB","Squared"],["A_pb"],[1]], ""],
           ['cheby1','BP',['fS','F_pb','F_pb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_pb"],[1]], ""],
           ['cheby1','BS',['fS','F_pb','F_pb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_pb"],[1]], ""],
           ['cheby2','LP',['fS','F_sb'],[48000,9600],True,True,"unit",[["dB","Squared"],["A_sb"],[60]], ""],
           ['cheby2','HP',['fS','F_sb'],[48000,14400],True,True,"unit",[["dB","Squared"],["A_sb"],[60]], ""],
           ['cheby2','BP',['fS','F_sb','F_sb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_sb"],[60]], ""],
           ['cheby2','BS',['fS','F_sb','F_sb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_sb"],[60]], ""]
                                )
        self.DEBUG = DEBUG                                              
        self.initUI()
        """
        choose_design_list[0]: Label / Design Method (string)
        choose_design_list[1]: Response Type ('rt', string)
        -- Frequency Specifications         
        choose_design_list[2]: Label Frequencies (list of strings)
        choose_design_list[3]: Frequencies (list of numbers) 
        choose_design_list[4]: Flag, Enable Min (???) (Boolean)
        choose_design_list[5]: Flag, Check Manual Order (Boolean)
        -- Amplitude / Weight Specifications        
        choose_design_list[6]: Selector (string):
            'txt' -> 
                choose_design_list[7]: Text-Info (string)
             'unit' -> 
                choose_design_list[7]: List of lists for Gains containing
                                            [Units, Labels, Defaultvalues]
        choose_design_list[8]: Infostring
        """
        
    def initUI(self): 
        """
        Create all widgets:

        sf : Select Filter with response type rt (LP, ...), 
              filter type ft (IIR, ...), and design method dm (cheby1, ...)
        fo : Filter Order (numeric or 'min')
        fs : Frequency Specifications 
        ms : Magnitude Specifications with the subwidgets
            txt : only text field for comments / instruction
            val : infostring (title), Label, value
            unt : unit, label, value

        """ 

        self.sf = SelectFilter.SelectFilter(DEBUG = True)
        self.fo = filterOrder.FilterOrder(DEBUG = False)
        self.fs = UnitBox.UnitBox(title = "Frequency Specifications",
                    units = ["Hz", "Normalize 0 to 1", "kHz", "MHz", "GHz"],
                    labels = ['fS', 'F_pb', 'F_sb'])
        
        self.ms_amp = UnitBox.UnitBox(title = "Amplitude Specifications",
                                      units = ["dB","Squared"],
                                      labels = ["A_pb","A_sb"])
                                      
        self.ms_wgt = UnitBox.UnitBox(
                title = "Weight Specifications",
                units = "",
                labels = ["W_pb","W_sb"])
        self.ms_last = "unit"
        
        self.ms_txt = QtGui.QLabel(self)
        self.ms_txt.setText("Enter a weight value for each band below")
        self.ms_txt.setWordWrap(True)
        # Magnitude Widgets not needed at the moment are made 
        # invisible but are always present!
        self.ms_txt.setVisible(False)
        self.ms_wgt.setVisible(True)
        self.ms_amp.setVisible(False)
        """
        LAYOUT      
        """
        self.layout=QtGui.QGridLayout()
        self.layout.addWidget(self.sf,0,0)  # Design method (IIR - ellip, ...)
        self.layout.addWidget(self.fo,1,0)  # Filter order
        self.layout.addWidget(self.fs,2,0)  # Freq. specifications
        self.layout.addWidget(self.ms_wgt,3,0)   #       - value
        self.layout.addWidget(self.ms_amp,4,0)   #       - amplitudes
        self.layout.addWidget(self.ms_txt,5,0)  # Mag. Spec. - text
        
        self.setLayout(self.layout)
        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        # Call chooseDesignMethod every time filter selection is changed: 
        self.fo.chkMin.clicked.connect(self.chooseDesignMethod)#rebuildMag)
        self.sf.comboResponseType.activated.connect(self.chooseDesignMethod)
        self.sf.comboFilterType.activated.connect(self.chooseDesignMethod)
        self.sf.comboDesignMethod.activated.connect(self.chooseDesignMethod)

        self.chooseDesignMethod() # first time initialization
        
    def chooseDesignMethod(self):
        """
        Depending on SelectFilter and frequency specs, the values of the 
        widgets fo, fs are recreated. For widget ms, the visibility is changed
        as well.
        """

        if self.DEBUG:
            print("=== chooseParams.chooseDesignMethod ===")
            print("curFilter:", db.gD["curFilter"])
        rt = db.gD["curFilter"]["rt"]
        ft = db.gD["curFilter"]["ft"]
        dm = db.gD["curFilter"]["dm"]
        fo = db.gD["curFilter"]["fo"]
        
#        myFilt = db.gD['curFilter']['rt']
        myLabels = db.gD['filterTree'][rt][ft][dm][fo]
        print('myLabels:', myLabels)
        freqLabels = [l for l in myLabels if l[0] == 'F']
        ampLabels = [l for l in myLabels if l[0] == 'A']
        weightLabels = [l for l in myLabels if l[0] == 'W']
        
        j=0
        found = False        
        while not found:
            if self.choose_design_list[j][0]== db.gD["curFilter"]["dm"] \
            and self.choose_design_list[j][1] == db.gD["curFilter"]["rt"]:
                found = True
                freqLabels = self.choose_design_list[j][2]
                freqSpecs = self.choose_design_list[j][3]
                enableMin = self.choose_design_list[j][4]  
                manOrder = self.choose_design_list[j][5]
                typeTxtbox = self.choose_design_list[j][6]                
                lstA_W_T = self.choose_design_list[j][7]
                self.infoText = self.choose_design_list[j][8]
            j += 1
  
        self.rebuildFrequFiltOrd(freqLabels, freqSpecs, 
                                 enMin = enableMin, checkMan = manOrder)
        self.rebuildMag(typeTxtbox, lstA_W_T)
        self.setLayout(self.layout)
        
        
    def rebuildFrequFiltOrd(self,liste=[],defaults=[],enMin=True,checkMan=True):
        """
        Auxiliary function for updating frequency specifications and the 
        frequency order widget
        """
        self.fs.set(newLabels = liste)#, newDefaults = defaults)
        self.fo.chkMin.setEnabled(enMin)
        
    def rebuildMag(self,string,lstA_W_T=[]):
        """
        Auxiliary function for updating magnitude specifications
        """

        if string == "txt":  # only Info-Text
            self.ms_amp.setVisible(False)
            self.ms_wgt.setVisible(False)
            self.ms_txt.setText(self.infoText)
            self.ms_txt.setVisible(True)
        if string == "unit" : # create subwidget with unit + label
            self.ms_amp.set(newLabels = lstA_W_T[1])#, newDefaults = lstA_W_T[2])
            self.ms_amp.setVisible(True)
            self.ms_wgt.setVisible(True)
            self.ms_txt.setVisible(False)
            
    def get(self):
        """
        Return a dict with the currently selected filter specifications 
        """
#        ret = {}
        db.gD["curFilter"]["fo"] # collect data from filter order widget
#        db.gD["curSpecs"].update(self.fs.get()) # collect data from frequ. spec. widget
#        db.gD["curSpecs"].update(self.ms_amp.get()) # magnitude specs with unit
#        db.gD["curSpecs"].update(self.ms_wgt.get()) # weight specs
        self.fs.update() # collect data from frequ. spec. widget
        self.ms_amp.update() # magnitude specs with unit
        self.ms_wgt.update() # weight specs
        
            
        if self.DEBUG: print(db.gD["curSpecs"])
#        return self.params  
        
#------------------------------------------------------------------------------ 
   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = ChooseParams()
    form.show()
    form.get()
   
    app.exec_()


   
        



 