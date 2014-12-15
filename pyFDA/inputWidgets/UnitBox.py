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
        self.labels = labels # list with labels for combobox
        self.defaults = defaults
        self.title = title
        
        self.spec = spec        
        self.units = [str(u) for u in units]
        
        self.qlabel = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()     
        
    def initUI(self): 
        self.WVLayout = QtGui.QVBoxLayout() # Widget layout   
        self.layout   = QtGui.QGridLayout()
        
        if self.title != "":
            bfont = QtGui.QFont()
            bfont.setBold(True)
#            bfont.setWeight(75)
            self.qtitle = QtGui.QLabel(self) # field for widget title
            self.qtitle.setText(str(self.title))
            self.qtitle.setFont(bfont)
            self.qtitle.setWordWrap(True)
            self.WVLayout.addWidget(self.qtitle)
        
        if self.units != []:
            self.lab_units=QtGui.QLabel(self)
            self.lab_units.setText("Units")
            self.combo_units=QtGui.QComboBox(self)
            self.combo_units.addItems(self.units)
            self.layout.addWidget(self.lab_units,0,0)
            self.layout.addWidget(self.combo_units,0,1)
        #self.layout.addWidget(self.qtitle, 0, 0, 2, 1) # span two columns

        # Create a gridLayout consisting of Labels and LineEdit fields
        # The number of created lines depends on the number of labels
        # qlabels is a list with references to the QLabel widgets, 
        # qlineedit contains references to the QLineEdit widgets
        
        for i in range(len(self.labels)):  # iterate over number of labels         
           
            self.qlabel.append(QtGui.QLabel(self))
            self.qlineedit.append(QtGui.QLineEdit(str(self.defaults[i])))
            self.qlabel[i].setText(self.labels[i])

            self.layout.addWidget(self.qlabel[i],(i+1),0)
            self.layout.addWidget(self.qlineedit[i],(i+1),1)
 
        self.WVLayout.addLayout(self.layout)
        self.setLayout(self.WVLayout)
#-------------------------------------------------------------        
    def set(self, title = "", newLabels = [], newDefaults = []):
        """
        Set title, labels, defaults - when number of elements changes, the 
        layout has to be rebuilt
        """
        print("Titel:",self.title)
        if title != "":
            print("Titel:",title)
            self.qtitle.setText(title) # new title
        maxLength = max(len(self.labels), len(newLabels))
    
        # Check whether the number of entries has changed
        for i in range(maxLength):
             # wenn keine elemente mehr in lab dann lösche restlichen Eingabefelder
            if (i > (len(newLabels)-1)):
                self.delElement(len(newLabels))

            # wenn in lab noch elemnete aber keine mehr in labels =>Einfügen    
            elif (i > (len(self.labels)-1)):
                self.addElement(i,newLabels[i],newDefaults[i])

            else:
                # when label has changed, update it and the default value
                if (self.labels[i]!=newLabels[i]):     
                    self.qlabel[i].setText(newLabels[i])
                    self.labels[i] = newLabels[i]
                    self.defaults[i] = newDefaults[i]
                    self.qlineedit[i].setText(str(newDefaults[i]))
    
        self.setLayout(self.WVLayout) # needed?
        
    def delElement(self,i):
        """
        Element with position i is deleted (qlabel and qlineedit)
        """
        self.layout.removeWidget(self.qlabel[i])
        self.layout.removeWidget(self.qlineedit[i])
        self.qlabel[i].deleteLater()
        del self.labels[i]
        del self.defaults[i]
        del self.qlabel[i]
        self.qlineedit[i].deleteLater()
        del self.qlineedit[i]  
        
    def addElement(self, i, new_label, new_default): 
        """
        Element with position i is appended (qlabel und qlineedit)
        """
        self.qlabel.append(QtGui.QLabel(self))
        self.labels.append(new_label)
        self.defaults.append(new_default)
        self.qlineedit.append(QtGui.QLineEdit(str (new_default)))
        self.qlabel[i].setText(new_label)
        self.layout.addWidget(self.qlabel[i],(i+1),0)
        self.layout.addWidget(self.qlineedit[i],(i+1),1)
      
    def get(self):
        """
        Return parameters as dict
        """

        dic = {}
        i=0
        for i in range(len(self.labels)):
            dic.update({self.labels[i]:float(self.qlineedit[i].text())})

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
#            dic.update({self.labels[i]:float(self.qlineedit[i].text())})
#            i=i+1
#        return dic
        
         
#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    units=['ab','cd','ef',]
    lab=['a','b','c',]
    defaults=[4,5,6]
    app = QtGui.QApplication(sys.argv)
    form=UnitBox(title = "hallo", units = units, labels = lab, defaults=defaults)#, spec="TEST")

    form.set(title = "Hallo", newLabels = ['a','b','c','d'], newDefaults = [1,2,3,10])
    form.set(newLabels = ['d','b','a'], newDefaults = [1,2,3])

    print form.get()
    form.show()
   
    app.exec_()
