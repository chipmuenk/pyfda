# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

xxx

@author: Julia Beike, Christian Münker
Created on 18.11.2013
Updated on Thur Dec 11 2014
"""
import sys
from PyQt4 import QtGui

class UnitBox(QtGui.QWidget):
    
    def __init__(self, title = "", units=[], labels=[], defaults=[], spec="", DEBUG = True):
        
        """
        Initialisierung
        units: sind die Einheiten die in der Combobox stehen sollen
        lab: Namen der Labels in einer Liste
        default: Dazugehörige Werte
        lab und default müssen immer gleiche länge sein!!! Überprüfung muss noch gemacht werden
        """
        super(UnitBox, self).__init__()   
        self.DEBUG = DEBUG
        self.labels = labels # list with combobox labels 
        self.qlabels = [] # list with QLabels instances (pointers)
        self.default_werte = defaults
        self.textfield = []

        self.spec = spec        
        self.unit=[str(i) for i in units]
        self.initUI()     
        
    def initUI(self): 
        
        self.layout=QtGui.QGridLayout()
        self.lab_units=QtGui.QLabel(self)
        self.lab_units.setText("Units")
        self.combo_units=QtGui.QComboBox(self)
        self.combo_units.addItems(self.unit)
        self.layout.addWidget(self.lab_units,0,0)
        self.layout.addWidget(self.combo_units,0,1)
        """
        Anzahl der Eingabefelder(Label+LineEdit) hängt von der bei der Initialisierung übergebenen Parametern ab
        alle labels werden in einer Liste gespeichert, alle TextFelder werden in einer Liste gespeichert
        """
        for i in range(len(self.labels)):  # iterate over number of labels         
           
            self.qlabels.append(QtGui.QLabel(self))
            self.textfield.append(QtGui.QLineEdit(str(self.default_werte[i])))
            self.qlabels[i].setText(self.labels[i])

            self.layout.addWidget(self.qlabels[i],(i+1),0)
            self.layout.addWidget(self.textfield[i],(i+1),1)
 
        self.setLayout(self.layout)
        
#-------------------------------------------------------------        
    def set(self, title = "", labels=[], defaults=[])  :
        """
        Set labels, defaults - when number of elements changes, the 
        layout has to be rebuilt
        """

        maximal = max(len(self.labels), len(labels))
    
        # Wird ein Eingabefeld hinzugefügt oder nicht?
        for i in range(maximal):
             # wenn keine elemente mehr in lab dann lösche restlichen Eingabefelder
            if (i > (len(labels)-1)):
                self.delElement(len(labels))

            # wenn in lab noch elemnete aber keine mehr in labels =>Einfügen    
            elif (i > (len(self.labels)-1)):
                self.addElement(i,labels[i],defaults[i])

            else:
                #wenn sich der Name des Labels ändert, defäult wert in Line Edit
                if (self.labels[i]!=labels[i]):  
                    
                    self.qlabels[i].setText(labels[i])
                    self.labels[i]=labels[i]
                    self.default_werte[i]=defaults[i]
                    self.textfield[i].setText(str(defaults[i]))
                    #wenn sich name des Labels nicht ändert, mache nichts
    
        self.setLayout(self.layout)
        
    def delElement(self,i):
        """
        Element with position i is deleted (qlabel and textfield)
        """
        self.layout.removeWidget(self.qlabels[i])
        self.layout.removeWidget(self.textfield[i])
        self.qlabels[i].deleteLater()
        del self.labels[i]
        del self.default_werte[i]
        del self.qlabels[i]
        self.textfield[i].deleteLater()
        del self.textfield[i]  
        
    def addElement(self, i, new_label, new_default): 
        """
        Element with position i is appended (qlabel und textfield)
        """
        self.qlabels.append(QtGui.QLabel(self))
        self.labels.append(new_label)
        self.default_werte.append(new_default)
        self.textfield.append(QtGui.QLineEdit(str (new_default)))
        self.qlabels[i].setText(new_label)
        self.layout.addWidget(self.qlabels[i],(i+1),0)
        self.layout.addWidget(self.textfield[i],(i+1),1)
      
    def get(self):
        """
        Return parameters as dict
        """
        dic={"Einheit"+self.spec:str(self.combo_units.currentText())}
        i=0
        while (i<len(self.labels)):
            dic.update({self.labels[i]:float(self.textfield[i].text())})
            i=i+1

        if self.DEBUG: 
            print("--- UnitBox.get() ---") 
            print(dic)
        return dic
 #------------------------------------------------------
#        
#    def get(self):
#        """
#        Return labels and parameters as dict
#        """
#        dic={}
#        i=0
#        while (i < len(self.labels)):
#            dic.update({self.labels[i]:float(self.textfield[i].text())})
#            i=i+1
#        return dic
        
         
#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    unit=['bf','bf','bf',]
    lab=['a','b','c',]
    default=[4,5,6]
    app = QtGui.QApplication(sys.argv)
    form=UnitBox(unit,lab,default,"TEST")
    form.set(['a','b','c','d'],[1,2,3,10])
    form.set(['d','b','a'],[1,2,3])
    i=form.get()
    print i
    form.show()
   
    app.exec_()
