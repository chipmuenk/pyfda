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
from __future__ import print_function, division, unicode_literals
import sys
from PyQt4 import QtGui

Don't use - this file has been replaced by unitBox !

class NumBox(QtGui.QWidget):
    
    def __init__(self, title = "", labels = [], defaults = [], DEBUG = True):
        """
        Parameters:
        
        title: Text above the input fields
        labels: list with names for the input fields (combobox)
        defaults: list with corresponding default values
        labels and defaults need to have same length!
        """
        super(NumBox, self).__init__()   
        self.DEBUG = DEBUG
        self.labels = labels
        self.defaults = defaults
        self.title = title
        
        self.qlabel = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()    
        
    def initUI(self):
        self.WVLayout=QtGui.QVBoxLayout() # Widget layout        
        if self.title != "":
            bfont = QtGui.QFont()
            bfont.setBold(True)
#            bfont.setWeight(75)
            self.qtitle = QtGui.QLabel(self) # field for widget title
            
            self.qtitle.setText(str(self.title))
            self.qtitle.setWordWrap(True)
            self.WVLayout.addWidget(self.qtitle)
        
        # Create a gridLayout consisting of Labels and LineEdit fields
        # The number of created lines depends on the number of labels
        # qlabels is a list with references to the QLabel widgets, 
        # qlineedit contains references to the QLineEdit widgets

        self.layout = QtGui.QGridLayout() # layout for input fields
        
        for i in range(len(self.labels)):  # iterate over number of labels         
            self.qlabel.append(QtGui.QLabel(self))
            self.qlabel[i].setText(self.labels[i])
            self.qlineedit.append(QtGui.QLineEdit(str(self.defaults[i])))

            self.layout.addWidget(self.qlabel[i], i, 0)
            self.layout.addWidget(self.qlineedit[i], i, 1)
            
        self.WVLayout.addLayout(self.layout)
        self.setLayout(self.WVLayout)

#-------------------------------------------------------------                
    def set(self, title = "", newLabels = [], newDefaults = []):
        """
        Set title, labels, defaults - when number of elements changes, the 
        layout has to be rebuilt
        """

        if title != "":
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

#    def set(self, labels = [], defaults = []):
#        """
#        Set title, labels, defaults - when number of elements changes, the 
#        layout has to be rebuilt
#        """
#
##        if self.title != "":
##            self.qtitle.setText(title) # new title
#        maxLength = max(len(self.labels), len(labels))
#
#        # Check whether the number of entries has changed
#        for i in range(maxLength):
#            # wenn keine elemente mehr in labels dann lösche restliche Eingabefelder
#            if (i > (len(labels)-1)):
#                self.delElement(len(labels))
#
#            # wenn in lab noch elemente aber keine mehr in self.labels => Einfügen    
#            elif (i > (len(self.labels)-1)):   
#                self.addElement(i,labels[i],defaults[i])   
#
#            else:
#                # when label has changed, update it and the default value
#                if (self.labels[i]!=labels[i]):  
#                    self.qlabel[i].setText(labels[i])
#                    self.labels[i]=labels[i]
#                    self.defaults[i]=defaults[i]
#                    self.qlineedit[i].setText(str(defaults[i]))
#                              
#        self.setLayout(self.WVLayout) # needed?

#-------------------------------------------------------------         
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
        self.qlineedit.append(QtGui.QLineEdit(str(new_default)))
        self.qlabel[i].setText(new_label)
        self.layout.addWidget(self.qlabel[i],(i+1),0)
        self.layout.addWidget(self.qlineedit[i],(i+1),1)
     
    def get(self):
        """
        Return labels and parameters as dict
        """
        dic={}
        i=0
        while (i < len(self.labels)):
            dic.update({self.labels[i]:float(self.qlineedit[i].text())})
            i=i+1
        if self.DEBUG: 
            print("--- NumBox.get() ---") 
            print(dic)    
        return dic

#------------------------------------------------------------------------------    

if __name__ == '__main__':
    import time
    title = "My Title"
    labels = ['a','b','c',]
    defaults = [4, 5, 6]
    app = QtGui.QApplication(sys.argv)
    form = NumBox(title = title, labels = labels, defaults = defaults)
    
    form.show()
    time.sleep(2)
    txt = form.get()
    print"____________ 1 _________________"
    print txt
    form.set(newLabels = ['a','a','a','a'], newDefaults = [1,1,1,1]) # dict with same labels
    txt = form.get()
    print"____________ 2 _________________"
    print txt
    form.set(newLabels = ['a','s'], newDefaults = [1,5])
    txt=form.get()
    print"____________ 3 _________________"
    print txt
    app.exec_()