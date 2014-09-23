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

class Txt_Box(QtGui.QWidget):
    
    def __init__(self, text,lab=[] ,default=[]):
        """
        Initialisierung
        text: ist der TExt der oberhalb der Eingabe stehen soll
        lab: Namen der Labels in einer Liste
        default: Dazugehörige Werte
        lab und default müssen immer gleiche länge sein!!! Überprüfung muss noch gemacht werden
        """
        super(Txt_Box, self).__init__()   
        self.lab_namen=lab
        self.labels= []
        self.default_werte=default
        self.textfield=[]
        #print self.default_werte
        self.txt=text
        self.initUI()
       
        
    def initUI(self): 
        anz=len(self.lab_namen)
        i=0
        
        self.layout=QtGui.QGridLayout()
        self.text=QtGui.QLabel(self)
        self.text.setText(str(self.txt))
        self.text.setWordWrap(True)
        self.WLayout=QtGui.QVBoxLayout()
        self.WLayout.addWidget(self.text)
        """
        Anzahl der Eingeabefelder(Label+LineEdit) hängt von der bei der Initialisierung übergebenen Parametern ab
        alle labels werden in einer Liste gespeichert, alle TextFelder werden in einer Liste gespeichert
        """
        while (i<anz):
           
            self.labels.append(QtGui.QLabel(self))
            self.textfield.append(QtGui.QLineEdit(str(self.default_werte[i])))
            self.labels[i].setText(self.lab_namen[i])

            self.layout.addWidget(self.labels[i],(i),0)
            self.layout.addWidget(self.textfield[i],(i),1)
            i=i+1
            
        self.WLayout.addLayout(self.layout)
        self.setLayout(self.WLayout)
        
    def Load_txt(self,text,lab=[] ,default=[])  :
        """
        Zum Ändern der Parameter(Anz Labels, Inhalt der Labels ...)
        """
        #print "------------------------------------"
       # print self.lab_namen
        i=0;
       # print "len neu"+str(len(lab))+":"
        #print lab
        #print "len alt"+str(len(self.lab_namen))+":"
        self.text.setText(text)
        #print self.lab_namen
        """
        Wird ein Eingabefeld hinzugefügt oder nicht?
        """
        if (len(self.lab_namen)>len(lab)):
            maximal=len(self.lab_namen)# hinzufügen
            minimal=len(lab) 
        else:
            maximal=len(lab)
            minimal=len(self.lab_namen)# nichts hinzufügen viell. löschen
        #print maximal    
        while (i<maximal):
            # wenn keine elemente mehr in lab dann lösche restlichen Eingabefelder
            if (i>(len(lab)-1)):
                #print 'löschen'
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
                   # print str(i)+":"+self.labels[i].text()+":"+self.textfield[i].text()
                   # print self.labels[i+1].text() + self.textfield[i+1].text()
                #wenn sich name des Labels nicht ändert, mache nichts
                 
             
                    
            i=i+1
            
       
        #print self.lab_namen
       
        self.setLayout(self.WLayout)
        #print "------------------------------------" 
        
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
        #print str(i)+":"+self.labels[i].text()+":"+self.textfield[i].text()
        self.layout.addWidget(self.labels[i],(i+1),0)
        self.layout.addWidget(self.textfield[i],(i+1),1)
     
    def get(self):
        """
        Rückgabe der Parameter
        """
        dic={}
        #namen=[]
       # data=[]
        i=0
        while (i<len(self.lab_namen)):
            dic.update({self.lab_namen[i]:float(self.textfield[i].text())})
            #namen.append(self.lab_namen[i])
            #data.append(float(self.textfield[i].text()))
            i=i+1
        print" TXTBOX"
        print dic
        return dic
    
if __name__ == '__main__':
    text="asdfa"
    lab=['a','b','c',]
    default=[4,5,6]
    app = QtGui.QApplication(sys.argv)
    form=Txt_Box(text,lab,default)
    
    form.show()
    txt=form.get()
    print"_____________________________"
    print txt
    form.Load_txt("HAllo",['a','a','a','a'],[1,1,1,1])
    txt=form.get()
    print"_____________________________"
    print txt
    form.Load_txt(text,['a','s'],[1,5])
    txt=form.get()
    print"_____________________________"
    print txt
    app.exec_()