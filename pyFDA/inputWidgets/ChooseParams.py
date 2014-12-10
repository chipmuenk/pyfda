# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 15:21:19 2013
Main Widget for entering filter specifications

@author: beike, Christian Münker
"""
import sys, os 
from PyQt4 import QtGui

# import databroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')
import databroker as db
    
import SelectFilter, widgetFilterOrder, UnitBox, NumBox # ResponseType, 


"""
Zur Eingabe aller Parameter und Einstellungen
"""

DEBUG = True

class ChooseParams(QtGui.QWidget):
    
    def __init__(self):
        super(ChooseParams, self).__init__()        
        # "Properties" of all filter types:
        self.choose_design_list=(
                               ['firls','LP',['Fs','F_pass','F_stop'],[48000,9600,12000],False,True,"val",["Enter a weight value for each band below",["W_pass","W_stop"],[1,1]]],
                               ['firls','HP',['Fs','F_pass','F_stop'],[48000,9600,12000],False,True,"val",["Enter a weight value for each band below",["W_pass","W_stop"],[1,1]]],
                               ['firls','BP',['Fs','F_stop1','F_pass1','F_stop2','F_pass2'],[48000,7200,9600,12000,14400],False,True,"val",["Enter a weight value for each band below",["W_stop1","W_pass","W_stop2"],[1,1,1]]],
                               ['firls','BS',['Fs','F_pass1','F_stop1','F_pass2','F_stop2'],[48000,7200,9600,12000,14400],False,True,"val",["Enter a weight value for each band below",["W_pass1","W_stop","W_pass2"],[1,1,1]]],
                               ['equiripple','LP',['Fs','F_pass','F_stop'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["W_pass","W_stop"],[1,1]]],
                               ['equiripple','HIL',['Fs','F_pass','F_stop'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["W_pass","W_stop"],[1,1]]],
                               ['equiripple','HP',['Fs','F_pass','F_stop'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["W_pass","W_stop"],[1,1]]],
                               ['equiripple','BP',['Fs','F_stop1','F_pass1','F_stop2','F_pass2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["W_stop1","W_pass","W_stop2"],[1,1,1]]],
                               ['equiripple','BS',['Fs','F_pass1','F_stop1','F_pass2','F_stop2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["W_pass1","W_stop","W_pass2"],[1,1,1]]],      
                               ['window','LP',['Fs','Fc'],[48000,10800],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
                               ['window','HP',['Fs','Fc'],[48000,10800],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
                               ['window','BP',['Fs','Fc1','Fc2'],[48000,8400,13200],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"],
                               ['window','BS',['Fs','Fc1','Fc2'],[48000,8400,13200],False,True,"txt","The attenuation at cutoff frequencies is fixed at 6 dB (half the passband gain)"], 
                               ['butter','LP',['Fs','Fc'],[48000,10800],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['butter','HP',['Fs','Fc'],[48000,10800],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['butter','BP',['Fs','Fc1','Fc2'],[48000,8400,13200],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['butter','BS',['Fs','Fc1','Fc2'],[48000,8400,13200],True,True,"txt","The attenuation at cutoff frequencies is fixed at 3 dB (half the passband power)"],
                               ['ellip','LP',['Fs','F_pass'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['ellip','HP',['Fs','F_pass'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['ellip','BP',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_stop1","A_pass","A_stop2"],[60,1,80]]],
                               ['ellip','BS',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass1","A_stop","A_pass2"],[5,60,1]]],
                               ['cheby1','LP',['Fs','F_pass'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['cheby1','HP',['Fs','F_pass'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['cheby1','BP',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['cheby1','BS',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
                               ['cheby2','LP',['Fs','F_pass'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['cheby2','HP',['Fs','F_pass'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass","A_stop"],[1,80]]],
                               ['cheby2','BP',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_stop1","A_pass","A_stop2"],[60,1,80]]],
                               ['cheby2','BS',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass1","A_stop","A_pass2"],[5,60,1]]]
                                )                                               
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

        sf : Select Filter with response type (LP, ...), filter type (IIR, ...), 
              and design method (cheby1, ...)
        fo : Filter Order (numeric or 'min')
        fs : Frequency Specifications 
        ms : Magnitude Specifications with the subwidgets
            txt : only text field for comments / instruction
            val : infostring (title), Label, value
            unt : unit, label, value

        """ 

        self.sf = SelectFilter.SelectFilter()
        self.fo = widgetFilterOrder.widgetFilterOrder()
        self.fs = UnitBox.UnitBox(
                    ["Hz", "Normalize 0 to 1", "kHz", "MHz", "GHz"],
                    ['Fs', 'F_pass', 'F_stop'], [48000,9600,12000], "Frequenz")
       
        self.ms_txt = QtGui.QLabel(self)
        self.ms_txt.setText("Enter a weight value for each band below")
        self.ms_txt.setWordWrap(True)
        self.ms_unt = UnitBox.UnitBox(["dB","Squared"],["A_pass","A_stop"],[1,80],"Magnitude")
        self.ms_val = NumBox.NumBox("Enter a weight value for each band below",["W_pass","W_stop"],[1,1])
        self.ms_last = "val"
        # Magnitude Widgets not needed at the moment are made 
        # invisible but are always present!
        self.ms_txt.setVisible(False)
        self.ms_val.setVisible(True)
        self.ms_unt.setVisible(False)
        """
        LAYOUT      
        """
        self.layout=QtGui.QGridLayout()
        self.layout.addWidget(self.sf,0,0)  # Design Method (IIR - ellip, ...)
        self.layout.addWidget(self.fo,2,0)  # Filter Order
        self.layout.addWidget(self.fs,3,0)  # Freq. Specifications
        self.layout.addWidget(self.ms_txt,4,0)  # Mag. Spec. - text
        self.layout.addWidget(self.ms_val,5,0)   #       - value
        self.layout.addWidget(self.ms_unt,6,0)   #       - unit
        
        self.setLayout(self.layout)
        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        # Call chooseDesignMethod every time filter selection is changed:      
        self.sf.comboResponseType.activated.connect(self.chooseDesignMethod)
        self.sf.comboFilterType.activated.connect(self.chooseDesignMethod)
        self.sf.comboDesignMethod.activated.connect(self.chooseDesignMethod)
        
    def chooseDesignMethod(self):
        """
        Depending on SelectFilter and frequency specs, the values of the 
        widgets fo, fs are recreated. For widget ms, the visibility is changed
        as well.
        """

        j=0
        found = False
        print(db.gD["curFilter"])#["dm"])
#        print(db.gD["curFilter"]["rt"])
        
        while not found:
           # print self.choose_design_list[j][0]+":"+self.choose_design_list[j][1]
            if self.choose_design_list[j][0]== db.gD["curFilter"]["dm"] \
            and self.choose_design_list[j][1] == db.gD["curFilter"]["rt"]:
                found = True
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
        # TODO: should this be db.gD["curSpecs"] ?
        ret = db.gD["curFilter"] # return selected filter design
        ret.update(self.fo.get())
        if DEBUG: print(ret)
        ret.update(self.fs.get())

        if self.ms_last=="unt":
            ret.update( self.ms_unt.get())
        if self.ms_last=="val" :
            ret.update( self.ms_val.get())
        if DEBUG: print(ret)
        return ret  
        
#------------------------------------------------------------------------------ 
   
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = ChooseParams()
    form.show()
    form.get()
   
    app.exec_()


   
        



 