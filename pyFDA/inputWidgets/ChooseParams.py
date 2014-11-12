# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 15:21:19 2013
MAINWINDOW

@author: beike
"""
import DesignMethod, ResponseType, widgetFilterOrder, UnitBox, NumBox
import sys 
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL
"""
Zur Eingabe aller Parameter und Einstellungen
"""
class ChooseParams(QtGui.QWidget):
    
    def __init__(self):
        super(ChooseParams, self).__init__()        
        self.initUI()
        # "Properties" of all filter types:
        self.choose_design_list=(
                               ['Least-squares','LP',['Fs','F_pass','F_stop'],[48000,9600,12000],False,True,"val",["Enter a weight value for each band below",["Wpass","Wstop"],[1,1]]],
                               ['Least-squares','HP',['Fs','F_pass','F_stop'],[48000,9600,12000],False,True,"val",["Enter a weight value for each band below",["Wpass","Wstop"],[1,1]]],
                               ['Least-squares','BP',['Fs','F_stop1','F_pass1','F_stop2','F_pass2'],[48000,7200,9600,12000,14400],False,True,"val",["Enter a weight value for each band below",["Wstop1","Wpass","Wstop2"],[1,1,1]]],
                               ['Least-squares','BS',['Fs','F_pass1','F_stop1','F_pass2','F_stop2'],[48000,7200,9600,12000,14400],False,True,"val",["Enter a weight value for each band below",["Wpass1","Wstop","Wpass2"],[1,1,1]]],
                               ['Equiripple','LP',['Fs','F_pass','F_stop'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["Wpass","Wstop"],[1,1]]],
                               ['Equiripple','HP',['Fs','F_pass','F_stop'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["Wpass","Wstop"],[1,1]]],
                               ['Equiripple','BP',['Fs','F_stop1','F_pass1','F_stop2','F_pass2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["Wstop1","Wpass","Wstop2"],[1,1,1]]],
                               ['Equiripple','BS',['Fs','F_pass1','F_stop1','F_pass2','F_stop2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["Wpass1","Wstop","Wpass2"],[1,1,1]]],      
                               ['Window','LP',['Fs','Fc'],[48000,10800],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
                               ['Window','HP',['Fs','Fc'],[48000,10800],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
                               ['Window','BP',['Fs','Fc1','Fc2'],[48000,8400,13200],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
                               ['Window','BS',['Fs','Fc1','Fc2'],[48000,8400,13200],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"], 
                               ['Butterworth','LP',['Fs','Fc'],[48000,10800],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['Butterworth','HP',['Fs','Fc'],[48000,10800],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['Butterworth','BP',['Fs','Fc1','Fc2'],[48000,8400,13200],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['Butterworth','BS',['Fs','Fc1','Fc2'],[48000,8400,13200],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['Elliptic','LP',['Fs','F_pass'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['Elliptic','HP',['Fs','F_pass'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['Elliptic','BP',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_stop1","A_pass","A_stop2"],[60,1,80]]],
                               ['Elliptic','BS',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass1","A_stop","A_pass2"],[5,60,1]]],
                               ['Chebychev 1','LP',['Fs','F_pass'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['Chebychev 1','HP',['Fs','F_pass'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['Chebychev 1','BP',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['Chebychev 1','BS',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['Chebychev 2','LP',['Fs','F_pass'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['Chebychev 2','HP',['Fs','F_pass'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['Chebychev 2','BP',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_stop1","A_pass","A_stop2"],[60,1,80]]],
                               ['Chebychev 2','BS',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass1","A_stop","A_pass2"],[5,60,1]]]
                                )                                               
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
             'unt' -> 
                choose_design_list[7]: List of lists for Gains containing
                                            [Units, Labels, Defaultvalues]
             'val' -> 
                choose_design_list[7]: List of lists for Weights containing
                                            [Infostring, Labels, Defaultvalues]
        """
        
    def initUI(self): 
        """
        Create all widgets:
        rt : Response Type (LP / HP / BP / BS)
        dm : Design Method (IIR / FIR)
        fo : Filter Order (numeric or 'min')
        fs : Frequency Specifications 
        ms : Magnitude Specifications with the subwidgets
            txt : only text field for comments / instruction
            val : infostring (title), Label, value
            unt : unit, label, value

        """ 

        self.dm = DesignMethod.DesignMethod()
        self.rt = ResponseType.ResponseType(["Lowpass","Highpass",
                                             "Bandpass","Bandstop"])
        self.fo = widgetFilterOrder.widgetFilterOrder()
        self.fs = UnitBox.UnitBox(
                    ["Hz", "Normalize 0 to 1", "kHz", "MHz", "GHz"],
                    ['Fs', 'F_pass', 'F_stop'], [48000,9600,12000], "Frequenz")
       
        self.ms_txt = QtGui.QLabel(self)
        self.ms_txt.setText("Enter a weight value for each band below")
        self.ms_txt.setWordWrap(True)
        self.ms_unt = UnitBox.UnitBox(["dB","Squared"],["A_pass","A_stop"],[1,80],"Magnitude")
        self.ms_val = NumBox.NumBox("Enter a weight value for each band below",["Wpass","Wstop"],[1,1])
        self.ms_last = "val"
        # Magnitude Widgets, that are not needed at the moment are made 
        # invisible but are always present!
        self.ms_txt.setVisible(False)
        self.ms_val.setVisible(True)
        self.ms_unt.setVisible(False)
        """
        LAYOUT      
        """
        self.layout=QtGui.QGridLayout()
        self.layout.addWidget(self.dm,0,0)  # Design Method (IIR - ellip, ...)
        self.layout.addWidget(self.rt,1,0)  # Response Type (LP, HP, ...)
        self.layout.addWidget(self.fo,2,0)  # Filter Order
        self.layout.addWidget(self.fs,3,0)  # Freq. Specifications
        self.layout.addWidget(self.ms_txt,4,0)  # Mag. Spec. - text
        self.layout.addWidget(self.ms_val,5,0)   #       - value
        self.layout.addWidget(self.ms_unt,6,0)   #       - unit
        
        self.setLayout(self.layout)
        """
        SIGNAL
        """
        # Call chooseDesignMethod every time filter design method or 
        # filter type is changed 
        self.connect(self.dm.comboDesignMethod, SIGNAL('activated(QString)'),
                     self.chooseDesignMethod)
        self.connect(self.dm.comboFilterType, SIGNAL('activated(QString)'),
                     self.chooseDesignMethod)
        
    def chooseDesignMethod(self):
        """
        je nach DesignMethode und Frequenz werden die Werte der Widgets do,ds 
        neu gesetzt bzw bei ms auch noch die Sichtbarkeit verändert
        """
        #print "-----------------------------------------"
        a=self.rt.get()
        resp_type=a["Response Type"]
       
        filtname=self.dm.comboDesignMethod.currentText()
        j=i=0
        while i==0:
           # print self.choose_design_list[j][0]+":"+self.choose_design_list[j][1]
            if self.choose_design_list[j][0]==filtname and self.choose_design_list[j][1]==resp_type:
                i=1
                choosen=self.choose_design_list[j][2:]
            j=j+1
        #print "-----------------------------------------"   
        self.rebuildFrequFiltOrd(choosen[0],choosen[1],choosen[2],choosen[3])
        self.rebuildMag(choosen[4],choosen[5])
        self.setLayout(self.layout)
        
        
    def rebuildFrequFiltOrd(self,liste=[],default=[],enMin=True,checkMan=True):
        """
        Hilfsfunktion zur Aktualisierung des Frequenz-Widget und der FilterOrdnung
        """
        self.fs.set(liste, default)
        self.fo.chkMin.setEnabled(enMin)
        self.fo.chkManual.setChecked(checkMan)
        
    def rebuildMag(self,string,liste=[]):
        """
        Hilfsfunktion zur Aktualisierung der Magnitude Specifications
        """
        #print "_________________________"
       # print liste
       # print string
       # print"_________________________"
        if string == "txt":  # only Info-Text
            self.ms_txt.setText(liste)
            self.ms_txt.setVisible(True)
            self.ms_unt.setVisible(False)
            self.ms_val.setVisible(False)
            self.ms_last="txt"
        if string == "unt" : # create subwidget with unit + label
            self.ms_unt.set(liste[1],liste[2])
            self.ms_unt.setVisible(True)
            self.ms_val.setVisible(False)
            self.ms_txt.setVisible(False)
            self.ms_last="unt"
        if string == "val" :  # create subwidget with title, unit + label
            self.ms_val.set(liste[0],liste[1],liste[2])
            self.ms_val.setVisible(True)
            self.ms_txt.setVisible(False)
            self.ms_unt.setVisible(False)
            self.ms_last="val"
            
    def get(self):
        """
        Return a dict with the currently selected filter specifications 
        """
        
        ret={}
        ret.update(self.rt.get())
        print ret
        ret.update(self.dm.get())
        print ret
        ret.update(self.fo.get())
        print ret
        ret.update(self.fs.get())
         

        if self.ms_last=="unt":
            ret.update( self.ms_unt.get())
        if self.ms_last=="val" :
            ret.update( self.ms_val.get())
        print ret
        return ret  
        
   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = ChooseParams()
    form.show()
    form.get()
   
    app.exec_()


   
        



 