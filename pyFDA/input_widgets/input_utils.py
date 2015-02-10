# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

input_utils.py

@author: Christian Münker
Created on 23.1.2015
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui, QtCore

class InputUtils(QtGui.QWidget):
    
    def __init__(self, specs, title = "", units=[], labels=[], DEBUG = True):
        
        """
        Initialisierung
        units: sind die Einheiten die in der Combobox stehen sollen
        lab: Namen der Labels in einer Liste
        """
        super(InputUtils, self).__init__()   
        self.DEBUG = DEBUG
        self.specs = specs  # dictionary for storing the specifications
        self.labels = labels # list with labels for combobox
        self.title = title
            
        self.units = [str(u) for u in units] # collect unit strings in list
        
#-------------------------------------------------------------        
    def setEntries(self, title = "", newLabels = []):
        """
        Set labels, defaults - when number of elements changes, the 
        layout has to be rebuilt
        """
        if self.DEBUG: print("UnitBox.Titel:",self.title)
        if title != "":
            self.qtitle.setText(title) # new title
    
        # Check whether the number of entries has changed
        for i in range(max(len(self.labels), len(newLabels))):
             # newLabels is shorter than labels -> delete the difference
            if (i > (len(newLabels)-1)):
                self.delElement(len(newLabels))

            # newLabels is longer than existing labels -> create new ones!   
            elif (i > (len(self.labels)-1)):
                self.addElement(i,newLabels[i])

            else:
                # when label has changed, update it and the default value
                if (self.labels[i]!=newLabels[i]):     
                    self.qlabel[i].setText(newLabels[i])
                    self.labels[i] = newLabels[i]
                    self.qlineedit[i].setText(str(fb.fil[0][newLabels[i]]))
                            
    def delEntry(self,i):
        """
        Element with position i is deleted (qlabel and qlineedit)
        """
        self.layout.removeWidget(self.qlabel[i])
        self.layout.removeWidget(self.qlineedit[i])
        self.qlabel[i].deleteLater()
        del self.labels[i]
        del self.qlabel[i]
        self.qlineedit[i].deleteLater()
        del self.qlineedit[i]  
        
    def addEntry(self, i, newLabel): 
        """
        Entry with position i is appended (qlabel und qlineedit)
        """
        self.qlabel.append(QtGui.QLabel(self))
        self.labels.append(newLabel)
        self.qlineedit.append(QtGui.QLineEdit(str(fb.fil[0][newLabel])))
        self.qlabel[i].setText(newLabel)
        self.layout.addWidget(self.qlabel[i],(i+1),0)
        self.layout.addWidget(self.qlineedit[i],(i+1),1)
      
    def reloadEntries(self):
        """
        Reload textfields from global dictionary to update changed weight
        settings etc.
        """
        for i in range(len(self.labels)):
            self.qlineedit[i].setText(str(fb.fil[0][self.labels[i]]))

    def saveEntries(self):
        """
        Save specification entries in dict fb.fil[0]
        """
        for i in range(len(self.labels)):
            fb.fil[0].update(
                            {self.labels[i]:float(self.qlineedit[i].text())})
    
