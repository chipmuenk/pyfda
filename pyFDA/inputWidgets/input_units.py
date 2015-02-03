# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

xxx

@author: Julia Beike, Christian Münker
Created on 18.11.2013
Updated on Thur Dec 11 2014
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui, QtCore

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb


class InputUnits(QtGui.QWidget): #QtGui.QWidget, 
    
    def __init__(self, title = "", units=[], labels=[], DEBUG = True):
        
        """
        Initialisierung
        units: sind die Einheiten die in der Combobox stehen sollen
        lab: Namen der Labels in einer Liste
        """
        super(InputUnits, self).__init__()   
        self.DEBUG = DEBUG
        self.labels = labels # list with labels for combobox
        self.title = title
            
        self.units = [str(u) for u in units] # collect unit strings in list
        
        self.qlabel = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()     
        
    def initUI(self): 
        self.WVLayout = QtGui.QVBoxLayout() # Widget vertical layout  
        self.layout   = QtGui.QGridLayout() # sublayout for spec fields
        
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
            self.layout.addWidget(self.combo_units,0,1, QtCore.Qt.AlignLeft)

        #self.layout.addWidget(self.qtitle, 0, 0, 2, 1) # span two columns

        # Create a gridLayout consisting of Labels and LineEdit fields
        # The number of created lines depends on the number of labels
        # qlabels is a list with references to the QLabel widgets, 
        # qlineedit contains references to the QLineEdit widgets

        # iterate over number of labels and fill in values        
        for i in range(len(self.labels)):        
           
            self.qlabel.append(QtGui.QLabel(self))
            self.qlabel[i].setText(self.labels[i])
            self.qlineedit.append(QtGui.QLineEdit(str(
                                        fb.gD['selFilter'][self.labels[i]])))

            self.layout.addWidget(self.qlabel[i],(i+1),0)
            self.layout.addWidget(self.qlineedit[i],(i+1),1)
        
        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.layout)
        
        self.WVLayout.addWidget(sfFrame)
#        self.WVLayout.addLayout(self.layout)

        self.setLayout(self.WVLayout)
#        
#        mainLayout = QtGui.QHBoxLayout()
#        mainLayout.addWidget(sfFrame)
#        self.setLayout(mainLayout)
        
        # SIGNALS & SLOTS
        # TODO: not working yet
        # Call update every time a field is edited: 
#        self.qlineedit.editingFinished.connect(self.update)

    
    def rtLabel(self, label):
        """
        Rich text labels: Format labels with HTML tags, replacing '_' by 
        HTML subscript tags
        """
        #"<b><i>{0}</i></b>".format(newLabels[i])) # update label
        if "_" in label:
            label = label.replace('_', '<sub>') 
            label += "</sub>"
        htmlLabel = "<b><i>"+label+"</i></b>"
        return htmlLabel
#-------------------------------------------------------------        
    def setEntries(self, title = "", newLabels = []):
        """
        Set title, labels, defaults - when number of elements changes, the 
        layout has to be rebuilt
        """
        if self.DEBUG: print("UnitBox.Titel:",self.title)
        if title != "":
            self.qtitle.setText(title) # new title
    
        # Check whether the number of entries has changed
        for i in range(max(len(self.labels), len(newLabels))):
             # newLabels is shorter than labels -> delete the difference
            if (i > (len(newLabels)-1)):
                self._delEntry(len(newLabels))

            # newLabels is longer than existing labels -> create new ones!   
            elif (i > (len(self.labels)-1)):
                self._addEntry(i,newLabels[i])

            else:
                # when label has changed, update it and the default value
                if (self.labels[i]!=newLabels[i]):     
                    self.qlabel[i].setText(self.rtLabel(newLabels[i]))
                    self.labels[i] = newLabels[i]
                    self.qlineedit[i].setText(str(fb.gD['selFilter'][newLabels[i]]))
                            
    def _delEntry(self,i):
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
        
    def _addEntry(self, i, newLabel): 
        """
        Element with position i is appended (qlabel und qlineedit)
        """
        self.qlabel.append(QtGui.QLabel(self))
        self.labels.append(newLabel)
        self.qlineedit.append(QtGui.QLineEdit(str(fb.gD['selFilter'][newLabel])))
        self.qlabel[i].setText(self.rtLabel(newLabel))
        self.layout.addWidget(self.qlabel[i],(i+1),0)
        self.layout.addWidget(self.qlineedit[i],(i+1),1)
      
    def loadEntries(self):
        """
        Reload textfields from global dictionary to update changed weight
        settings etc.
        """
        for i in range(len(self.labels)):
            self.qlineedit[i].setText(str(fb.gD['selFilter'][self.labels[i]]))


    def storeEntries(self):
        """
        Store specification entries in dict fb.gD['selFilter']
        """
        for i in range(len(self.labels)):
            fb.gD['selFilter'].update(
                            {self.labels[i]:float(self.qlineedit[i].text())})
    
#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    units = ['dB','V','W',]
    lab = ['A_sb','A_sb','A_sb2',]
    app = QtGui.QApplication(sys.argv)
    form = InputUnits(title = "Amplitudes", units = units, labels = lab)#, spec="TEST")

    form.setEntries(title = "Gewichte", newLabels = ['W_sb','W_sb2','W_pb','W_pb2'])
    form.setEntries(newLabels = ['W_pb','W_pb2'])

    form.show()
   
    app.exec_()
