# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

input_utils.py

@author: Christian Münker
Created on 23.1.2015
"""
from __future__ import print_function, division, unicode_literals
import sys #, os
from collections import OrderedDict
from PyQt4 import QtGui, QtCore

class InputFreqs(QtGui.QWidget):
    """
    Build and update widget for entering the frequency 
    specifications like F_sb, F_pb etc.
    """
    
    def __init__(self, specs, DEBUG = True):
        
        """
        Initialize
        specs: A dictionary containing all the specs
        labels: Names of the frequency spec labels
        """
        super(InputFreqs, self).__init__()   
        self.DEBUG = DEBUG
        self.specs = specs  # dictionary containing _all_ specifications of the
                            # currently selected filter
        self.labels = []    # list with labels for combobox

        self.qlabel = []    # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()     
        
    def initUI(self): 
        self.WVLayout = QtGui.QVBoxLayout() # Widget vertical layout  
        self.layout   = QtGui.QGridLayout() # sublayout for spec fields

        title = "Frequency Specifications"      
        units = ["Hz", "Normalize 0 to 1", "kHz", "MHz", "GHz"]
        self.unitsf = OrderedDict([
        ('Normalized', 0.5),
        ('Hz', 1.),
        ('kHz', 1000.),
        ('MHz', 1.e6),
        ('GHz', 1.e9)
        ])
        self.idxOld = 0 # index of comboUnits before last change
        
        if title != "":
            bfont = QtGui.QFont()
            bfont.setBold(True)
#            bfont.setWeight(75)
            self.qtitle = QtGui.QLabel(self) # field for widget title
            self.qtitle.setText(str(title))
            self.qtitle.setFont(bfont)
            self.qtitle.setWordWrap(True)
            self.WVLayout.addWidget(self.qtitle)
        
        if units != []:
            self.labelUnits=QtGui.QLabel(self)
            self.labelUnits.setText("Units")
            
            self.f_S = self.specs["f_S"]            
            self.editF_S = QtGui.QLineEdit()
            self.editF_S.setText(str(self.f_S))
            self.editF_S.setObjectName("f_S")
            self.editF_S.editingFinished.connect(self.freqUnits)


            self.comboUnits=QtGui.QComboBox(self)
            self.comboUnits.setObjectName("comboUnits")
            self.comboUnits.addItems(self.unitsf.keys())
            self.comboUnits.setCurrentIndex(self.idxOld)

            self.layout.addWidget(self.labelUnits,0,0)
            self.layout.addWidget(self.comboUnits,0,1, QtCore.Qt.AlignLeft)
            self.layout.addWidget(self.editF_S,0,2)

        #self.layout.addWidget(self.qtitle, 0, 0, 2, 1) # span two columns

        # Create a gridLayout consisting of Labels and LineEdit fields
        # The number of created lines depends on the number of labels
        # qlabels is a list with references to the QLabel widgets, 
        # qlineedit contains references to the QLineEdit widgets

        # - Build a list from all entries in the specs dictionary starting 
        #   with "F" (= frequency specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget        
        newLabels = [l for l in self.specs if l[0] == 'F']
        self.setEntries(newLabels = newLabels)
#        for i in range(len(self.labels)):        
#           
#            self.qlabel.append(QtGui.QLabel(self))
#            self.qlabel[i].setText(self.labels[i])
#            self.qlineedit.append(QtGui.QLineEdit(str(
#                                        self.specs[self.labels[i]])))
#            self.qlineedit[i].editingFinished.connect(self.freqUnits)
#
#            self.layout.addWidget(self.qlabel[i],(i+1),0)
#            self.layout.addWidget(self.qlineedit[i],(i+1),1)
        
        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.layout)
        
        self.WVLayout.addWidget(sfFrame)
#        self.WVLayout.addLayout(self.layout) # no frame

        self.setLayout(self.WVLayout)
#        
#        mainLayout = QtGui.QHBoxLayout()
#        mainLayout.addWidget(sfFrame)
#        self.setLayout(mainLayout)
        
        # SIGNALS & SLOTS
        # Every time a field is edited, call self.freqUnits - the signal is
        # constructed in _addEntry
        self.comboUnits.currentIndexChanged.connect(self.freqUnits)

    def mousePressEvent(self, event):
        """
        Do something every time a mouse event happens inside this widget - but 
        only if the event isn't swallowed by a child widget!!
        """
        print ("InputFreqs Mouse Press")
        super(InputFreqs, self).mousePressEvent(event)        

#-------------------------------------------------------------        
    def freqUnits(self):
        
        idx = self.comboUnits.currentIndex()
        freqParams = [l for l in self.specs if l[0] == 'F']
        self.f_S = float(self.editF_S.text())
        sender = self.sender()
#        self.statusBar().showMessage(sender.text() + ' was pressed')
        print(sender.objectName() + ' was edited\n=======================')
        if sender.objectName() == "f_S" and self.f_S != 0:
            self.specs['f_S'] = self.f_S
            for i in range(len(self.labels)):
#                   print(float(self.qlineedit[i].text()))
                f = self.specs[self.qlineedit[i].objectName()]
                self.qlineedit[i].setText(str(f * self.f_S))        

#                    self.specs[F] = self.specs[F] / self.unitsf[unit]
        elif sender.objectName() == "comboUnits" and idx != self.idxOld: # unit  has changed
            self.scale = self.comboUnits.itemData(idx)
            unit = str(self.comboUnits.itemText(idx))
#            if idx > 0: # not normalized
#                for F in freqParams:
#                    print(F, unit)
#                    self.specs[F] = self.specs[F] / self.unitsf[unit]

        else: # freq. spec textfield has been changed
            self.storeEntries()

        print(idx, self.f_S, freqParams)

        self.idxOld = idx
  
        
    
    def setEntries(self, title = "", newLabels = []):
        """
        Set labels, defaults - when number of elements changes, the 
        layout has to be rebuilt
        """
        if self.DEBUG: print("InputFreqs.Titel:",self.title)
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
                    self.qlabel[i].setText(newLabels[i])
                    self.labels[i] = newLabels[i]
                    self.qlineedit[i].setText(str(self.specs[newLabels[i]]))
                            
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
        Entry with position i is appended (qlabel und qlineedit)
        """
        self.qlabel.append(QtGui.QLabel(self))
        self.labels.append(newLabel)
        self.qlineedit.append(QtGui.QLineEdit(str(self.specs[newLabel])))
        self.qlineedit[i].editingFinished.connect(self.freqUnits)
        self.qlineedit[i].setObjectName(newLabel)

        self.qlabel[i].setText(newLabel)
        self.layout.addWidget(self.qlabel[i],(i+1),0)
        self.layout.addWidget(self.qlineedit[i],(i+1),1)
      
    def loadEntries(self):
        """
        Reload textfields from global dictionary to update changed weight
        settings etc.
        """
        for i in range(len(self.labels)):
            self.qlineedit[i].setText(str(self.specs[self.labels[i]]))

    def storeEntries(self):
        """
        Store specification entries in dict fb.gD['selFilter']
        Entries are normalized with sampling frequency self.f_S !
        """
        for i in range(len(self.labels)):
            self.specs.update(
                {self.labels[i]:float(self.qlineedit[i].text())/self.f_S})
    
#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    lab = ['F_sb','F_sb','F_sb2']
    app = QtGui.QApplication(sys.argv)
    form = InputFreqs(labels = lab)#, spec="TEST")

    form.setEntries(title = "Gewichte", newLabels = ['W_sb','W_sb2','W_pb','W_pb2'])
    form.setEntries(newLabels = ['W_pb','W_pb2'])

    form.show()
   
    app.exec_()
