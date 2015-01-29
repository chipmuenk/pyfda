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
        self.qlabel = []    # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()     
        
    def initUI(self): 
        self.WVLayout = QtGui.QVBoxLayout() # Widget vertical layout  

        title = "Frequency Specifications"      
        self.unitsf = OrderedDict([
        ('Normalized to f_S/2', 0.5),
        ('Hz', 1.),
        ('kHz', 1000.),
        ('MHz', 1.e6),
        ('GHz', 1.e9)
        ])
        
        self.idxOld = 0 # index of comboUnits before last change
        

        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        self.qtitle = QtGui.QLabel(self) # field for widget title
        self.qtitle.setText(str(title))
        self.qtitle.setFont(bfont)
        self.qtitle.setWordWrap(True)
        self.WVLayout.addWidget(self.qtitle)    

        self.labelUnits=QtGui.QLabel(self)
        self.labelUnits.setText("Units")
        
        self.f_S = self.specs["f_S"]            
        self.editF_S = QtGui.QLineEdit()
        self.editF_S.setText(str(self.f_S))
        self.editF_S.setObjectName("f_S")

        self.labelF_S = QtGui.QLabel(self)
        self.labelF_S.setText("f_S")

        self.comboUnits = QtGui.QComboBox(self)
        self.comboUnits.setObjectName("comboUnits")
        self.comboUnits.addItems(self.unitsf.keys())
        self.comboUnits.setCurrentIndex(self.idxOld)
        
        self.butSort = QtGui.QPushButton(self)
        self.butSort.setText("Sort")
        self.butSort.setToolTip("Sort frequencies in ascending order.")       
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.comboUnits)
        self.hbox.addWidget(self.butSort)
        
        self.layout = QtGui.QGridLayout() # sublayout for spec fields
        self.layout.addWidget(self.labelUnits,0,0)
        self.layout.addLayout(self.hbox,0,1)
#        self.layout.addWidget(self.butSort,0,2, QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.labelF_S,1,0)
        self.layout.addWidget(self.editF_S,1,1)

        # Create a gridLayout consisting of QLabel and QLineEdit fields
        # The number of created lines depends on the number of labels

        # - Build a list from all entries in the specs dictionary starting 
        #   with "F" (= frequency specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget        
        newLabels = [l for l in self.specs if l[0] == 'F']
        self.setEntries(newLabels = newLabels)
        
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
        #   constructed in _addEntry
        self.comboUnits.currentIndexChanged.connect(self.freqUnits)
        self.editF_S.editingFinished.connect(self.freqUnits)
        self.butSort.clicked.connect(self._sortEntries)

    def mousePressEvent(self, event):
        """
        Do something every time a mouse event happens inside this widget - but 
        only if the event isn't swallowed by a child widget!!
        """
        print ("InputFreqs Mouse Press")
        super(InputFreqs, self).mousePressEvent(event)        

#-------------------------------------------------------------        
    def freqUnits(self):
        """
        Transform the 
        """        
        idx = self.comboUnits.currentIndex()
        freqSpecs = [l for l in self.specs if l[0] == 'F'] # list with freq. specs
        self.f_S = float(self.editF_S.text()) # sampling frequency
        sender = self.sender() # origin of signal that triggered the slot
        print(sender.objectName() + ' was edited\n=======================')

        if sender.objectName() == "f_S" and self.f_S != 0:
            self.specs['f_S'] = self.f_S
            for i in range(len(self.qlabel)):
                f = self.specs[self.qlineedit[i].objectName()]
                self.qlineedit[i].setText(str(f * self.f_S))

#                    self.specs[F] = self.specs[F] / self.unitsf[unit]
        elif sender.objectName() == "comboUnits" and idx != self.idxOld: # unit  has changed
            self.scale = self.comboUnits.itemData(idx)
            self.editF_S.setVisible(idx > 0) # only visible when not normalized
            self.labelF_S.setVisible(idx > 0)
            unit = str(self.comboUnits.itemText(idx))
#            if idx > 0: # not normalized
#                for F in freqParams:
#                    print(F, unit)
#                    self.specs[F] = self.specs[F] / self.unitsf[unit]

        else: # freq. spec textfield has been changed
            self.storeEntries()

        print(idx, self.f_S, freqSpecs)

        self.idxOld = idx
        
    
    def setEntries(self, newLabels = []):
        """
        Set labels and get corresponding values from filter dictionary.
        When number of elements changes, the layout of subwidget is rebuilt.
        """ 
        # Check whether the number of entries has changed
        for i in range(max(len(self.qlabel), len(newLabels))):
             # newLabels is shorter than qlabel -> delete the difference
            if (i > (len(newLabels)-1)):
                self._delEntry(len(newLabels))

            # newLabels is longer than existing qlabels -> create new ones!   
            elif (i > (len(self.qlabel)-1)):   
             self._addEntry(i,newLabels[i])

            else:
                # when entry has changed, update label and corresponding value
                if self.qlabel[i].text() != newLabels[i]:     
                    self.qlabel[i].setText(newLabels[i]) # update label

                    self.qlineedit[i].setText(str(self.specs[newLabels[i]]*self.f_S))
                    self.qlineedit[i].setObjectName(newLabels[i])  # update ID     
                     
    def _delEntry(self,i):
        """
        Delete entry number i from subwidget (QLabel and QLineEdit)
        """
        self.layout.removeWidget(self.qlabel[i])
        self.layout.removeWidget(self.qlineedit[i])

        self.qlabel[i].deleteLater()
        del self.qlabel[i]
        self.qlineedit[i].deleteLater()
        del self.qlineedit[i]  
        

    def _addEntry(self, i, newLabel): 
        """
        Append entry number i to subwidget (QLabel und QLineEdit)
        """
        self.qlabel.append(QtGui.QLabel(self))
        self.qlabel[i].setText(newLabel)
        
        self.qlineedit.append(QtGui.QLineEdit(str(self.specs[newLabel])))
        self.qlineedit[i].editingFinished.connect(self.freqUnits)
        self.qlineedit[i].setObjectName(newLabel)

        self.layout.addWidget(self.qlabel[i],(i+2),0)
        self.layout.addWidget(self.qlineedit[i],(i+2),1)
        
    def _sortEntries(self): 
        """
        Sort spec entries with ascending frequency
        """
        fSpecs = []
        for i in range(len(self.qlineedit)):
            fSpecs.append(self.qlineedit[i].text())
#        fSpecs = [f for f in self.qlineedit.text()]        
        
        fSpecs.sort()
        
        for i in range(len(self.qlineedit)):
            self.qlineedit[i].setText(fSpecs[i])
        self.storeEntries()
      
    def loadEntries(self):
        """
        Reload textfields from filter dictionary to update changed settings 
        """
        for i in range(len(self.qlabels)): 
            self.qlineedit[i].setText(str(self.specs[self.qlabel[i].text()]))

    def storeEntries(self):
        """
        Store specification entries in filter dictionary
        Entries are normalized with sampling frequency self.f_S !
        The scale factor (khz, ...) is contained neither in f_S nor the specs
        hence, it cancels out.
        """
        for i in range(len(self.qlabel)): 
            self.specs.update(
                {self.qlabel[i].text():float(self.qlineedit[i].text())/self.f_S})

    
#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    lab = ['F_sb','F_sb','F_sb2']
    app = QtGui.QApplication(sys.argv)
    form = InputFreqs(specs = fb.gd["curFilter"])#, spec="TEST")

    form.setEntries(title = "Gewichte", newLabels = ['W_sb','W_sb2','W_pb','W_pb2'])
    form.setEntries(newLabels = ['W_pb','W_pb2'])

    form.show()
   
    app.exec_()
