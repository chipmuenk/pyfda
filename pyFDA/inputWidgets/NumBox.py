# -*- coding: utf-8 -*-
"""


Create a titled box with labelled numeric entry fields.
Default values are provided as well. The set() method can change the number
of entry fields as well as the title. The get() method returns a dict with
the labels and values, 

@author: Julia Beike, Christian Münker
Created on 18.11.2013
Updated on Mon Nov 10 2014
"""
import sys
from PyQt4 import QtGui

class NumBox(QtGui.QWidget):
    
    def __init__(self, title, labels = [], defaults = [], DEBUG = True):
        """
        Initialisierung
        text: ist der Text, der oberhalb der Eingabe stehen soll
        labels: Namen der Labels in einer Liste
        defaults: Dazugehörige Werte
        labels und default müssen immer gleiche Länge haben!!! Überprüfung muss noch gemacht werden
        """
        super(NumBox, self).__init__()   
        self.DEBUG = DEBUG
        self.labels = labels
        self.qlables = [] # list with QLabels instances (pointers)
        self.default_werte = defaults
        self.textfield = []

        self.title = title
        self.initUI()    
        
    def initUI(self): 
        
        self.qtitle = QtGui.QLabel(self)
        self.qtitle.setText(str(self.title))
        self.qtitle.setWordWrap(True)
        
        self.WLayout=QtGui.QVBoxLayout()
        self.WLayout.addWidget(self.qtitle)
        """
        Anzahl der Eingeabefelder(Label+LineEdit) hängt von den bei der 
        Initialisierung übergebenen Parametern ab, alle Labels und TextFelder
        werden in je einer Liste gespeichert.
        """
        self.layout = QtGui.QGridLayout()
        for i in range(len(self.labels)):  # iterate over number of labels         
            self.qlables.append(QtGui.QLabel(self))
            self.textfield.append(QtGui.QLineEdit(str(self.default_werte[i])))
            self.qlables[i].setText(self.labels[i])

            self.layout.addWidget(self.qlables[i], i, 0)
            self.layout.addWidget(self.textfield[i], i, 1)
            
        self.WLayout.addLayout(self.layout)
        self.setLayout(self.WLayout)

#-------------------------------------------------------------                
    def set(self, title, labels = [], default = []):
        """
        Set title, labels, defaults - when number of elements changes, the 
        layout has to be rebuilt
        """
    

        self.qtitle.setText(title) # new title
        maximal = max(len(self.labels), len(labels))
#        minimal = min(len(self.labels), len(labels))

        # Wird ein Eingabefeld hinzugefügt oder nicht?
        for i in range(maximal):
            # wenn keine elemente mehr in labels dann lösche restliche Eingabefelder
            if (i > (len(labels)-1)):
                self.delElement(len(labels))

            # wenn in lab noch elemente aber keine mehr in self.labels => Einfügen    
            elif (i > (len(self.labels)-1)):   
                self.addElement(i,labels[i],default[i])   

            else:
                #wenn sich der Name des Labels ändert, default wert in Line Edit
                if (self.labels[i]!=labels[i]):  
                    
                    self.qlables[i].setText(labels[i])
                    self.labels[i]=labels[i]
                    self.default_werte[i]=default[i]
                    self.textfield[i].setText(str(default[i]))
                #wenn sich name des Labels nicht ändert, mache nichts
                              
        self.setLayout(self.WLayout)
        
    def delElement(self,i):
        """
        Element with position i is deleted (qlabel and textfield)
        """
        self.layout.removeWidget(self.qlables[i])
        self.layout.removeWidget(self.textfield[i])
        self.qlables[i].deleteLater()
        del self.labels[i]
        del self.default_werte[i]
        del self.qlables[i]
        self.textfield[i].deleteLater()
        del self.textfield[i]  
        
    def addElement(self, i, new_label, new_default):
        """
        Element with position i is appended (qlabel und textfield)
        """
        self.qlables.append(QtGui.QLabel(self))
        self.labels.append(new_label)
        
        self.default_werte.append(new_default)
        self.textfield.append(QtGui.QLineEdit(str(new_default)))
        self.qlables[i].setText(new_label)
        self.layout.addWidget(self.qlables[i],(i+1),0)
        self.layout.addWidget(self.textfield[i],(i+1),1)
     
    def get(self):
        """
        Return labels and parameters as dict
        """
        dic={}
        i=0
        while (i < len(self.labels)):
            dic.update({self.labels[i]:float(self.textfield[i].text())})
            i=i+1
        return dic

#------------------------------------------------------------------------------    

if __name__ == '__main__':
    import time
    title = "My Title"
    labels = ['a','b','c',]
    defaults = [4, 5, 6]
    app = QtGui.QApplication(sys.argv)
    form = NumBox(title, labels, defaults)
    
    form.show()
    time.sleep(2)
    txt = form.get()
    print"____________ 1 _________________"
    print txt
    form.set("Hallo",['a','a','a','a'],[1,1,1,1]) # dict with same labels
    txt = form.get()
    print"____________ 2 _________________"
    print txt
    form.set(title,['a','s'],[1,5])
    txt=form.get()
    print"____________ 3 _________________"
    print txt
    app.exec_()