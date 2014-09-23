# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 12:19:33 2013

@author: beike
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

@author: beike
"""
"""
Auswahl von DesignTyp,FilterMethode 
@author: Julia Beike
Datum:14.11.2013
"""
import sys
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import SIGNAL

class Unit_Box(QtGui.QWidget):
    
    def __init__(self, unit=[],lab=[] ,default=[],name=""):
        
        """
        Initialisierung
        units: sind die Einheiten die in der Combobox stehen sollen
        lab: Namen der Labels in einer Liste
        default: Dazugehörige Werte
        lab und default müssen immer gleiche länge sein!!! Überprüfung muss noch gemacht werden
        """
        super(Unit_Box, self).__init__()   
        self.lab_namen=lab
        self.labels= []
        self.name=name
       
        
        self.unit=[str(i) for i in unit]
        self.default_werte=default
        self.textfield=[]
        #print self.default_werte
        self.initUI()
       
        
    def initUI(self): 
        anz=len(self.lab_namen)
        i=0
        
        self.layout=QtGui.QGridLayout()
        self.lab_units=QtGui.QLabel(self)
        self.lab_units.setText("Units")
        self.combo_units=QtGui.QComboBox(self)
        self.combo_units.addItems(self.unit)
        self.layout.addWidget(self.lab_units,0,0)
        self.layout.addWidget(self.combo_units,0,1)
        """
        Anzahl der Eingeabefelder(Label+LineEdit) hängt von der bei der Initialisierung übergebenen Parametern ab
        alle labels werden in einer Liste gespeichert, alle TextFelder werden in einer Liste gespeichert
        """
        while (i<anz):
           
            self.labels.append(QtGui.QLabel(self))
            self.textfield.append(QtGui.QLineEdit(str(self.default_werte[i])))
            self.labels[i].setText(self.lab_namen[i])

            self.layout.addWidget(self.labels[i],(i+1),0)
            self.layout.addWidget(self.textfield[i],(i+1),1)
            i=i+1
 
 
        self.setLayout(self.layout)
        
    def Load_txt(self,lab=[] ,default=[])  :
        """
        Zum Ändern der Parameter(Anz Labels, Inhalt der Labels ...)
        """
        i=0;
        """
        Wird ein Eingabefeld hinzugefügt oder nicht?
        """
        if (len(self.lab_namen)>len(lab)):
            maximal=len(self.lab_namen)# hinzufügen
            #minimal=len(lab)
        else:
            maximal=len(lab)# nichts hinzufügen viell. löschen
            #minimal=len(self.lab_namen)
       # print maximal    
        while (i<maximal):
             # wenn keine elemente mehr in lab dann lösche restlichen Eingabefelder
            if (i>(len(lab)-1)):
             
                self.Loesche_elm(len(lab))
            # wenn in lab noch elemnete aber keine mehr in lab_namen =>Einfügen    
            elif (i>(len(self.lab_namen)-1)):
                self.add_elm(i,lab[i],default[i])

            else:
                #wenn sich der Name des Labels ändert, defäult wert in Line Edit
                if (self.lab_namen[i]!=lab[i]):  
                    
                    self.labels[i].setText(lab[i])
                    self.lab_namen[i]=lab[i]
                    self.default_werte[i]=default[i]
                    self.textfield[i].setText(str(default[i]))
                    #wenn sich name des Labels nicht ändert, mache nichts
                   # print self.labels[i+1].text() + self.textfield[i+1].text()
            i=i+1
            
       
       # print self.lab_namen

        self.setLayout(self.layout)
       # print "------------------------------------" 
        
    def Loesche_elm(self,i):
        
        """
        elm an pos i wird gelöscht (in labels und textfield)
        """
        self.layout.removeWidget(self.labels[i])
        self.layout.removeWidget(self.textfield[i])
        self.labels[i].deleteLater()
        del self.lab_namen[i]
        del self.default_werte[i]
        del self.labels[i]
        self.textfield[i].deleteLater()
        del self.textfield[i]  
        
    def add_elm(self,i,lab_name,defaultw)  : 
        
        """
        elm an pos i wird angefügt (in labels und textfield)
        """
        self.labels.append(QtGui.QLabel(self))
        self.lab_namen.append(lab_name)
        self.default_werte.append(defaultw)
        self.textfield.append(QtGui.QLineEdit(str (defaultw)))
        self.labels[i].setText(lab_name)
        # print str(i)+":"+self.labels[i].text()+":"+self.textfield[i].text()
        self.layout.addWidget(self.labels[i],(i+1),0)
        self.layout.addWidget(self.textfield[i],(i+1),1)
      
    def get(self):
        """
        Rückgabe der Parameter
        """
        dic={"Einheit"+self.name:str(self.combo_units.currentText())}
        #namen=[]
        #data=[]
        i=0
        while (i<len(self.lab_namen)):
            dic.update({self.lab_namen[i]:float(self.textfield[i].text())})
            #namen.append(self.lab_namen[i])
            #data.append(float(self.textfield[i].text()))
            i=i+1
        print dic
        return dic
         
 
    
if __name__ == '__main__':
    unit=['bf','bf','bf',]
    lab=['a','b','c',]
    default=[4,5,6]
    app = QtGui.QApplication(sys.argv)
    form=Unit_Box(unit,lab,default,"TEST")
    form.Load_txt(['a','b','c','d'],[1,2,3,10])
    form.Load_txt(['d','b','a'],[1,2,3])
    i=form.get()
    print i
    form.show()
   
    app.exec_()
